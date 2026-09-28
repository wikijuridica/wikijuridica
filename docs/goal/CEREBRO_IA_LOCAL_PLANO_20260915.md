# Cérebro (IA local): veredito, causa do travamento e plano de produção autônoma

> **Nota de 2026-09-24.** O plano do EnaEval (`docs/goal/enaeval/`) fixa a convivência deste cérebro com o serving do EnaEval até F3.O1 e o objetivo F3.O0 (Ollama na GPU): ver `docs/goal/enaeval/PONTE_CEREBRO_E_REDE_SOCIAL.md` e DEC-062.

> ## REGRA ZERO — LACUNA NÃO É LIMITE, É TRABALHO
>
> **Ordem do dono, 2026-09-15, vinculante para esta sessão e para todas as seguintes:**
>
> *"Se não está verificado, lance agentes para verificar. Nada de deixar para depois."*
> *"Se tiver lacunas, investigar. Se faltar dados, investigar. **Não tratar como limite, mas
> como dados a serem investigados e melhorar engenharia.**"*
> *"Enquanto não tiver 100% dos dados suficientes para executar, não terá plano."*
> *"É pura engenharia e não consultoria."* · *"Nenhuma decisão para o dono."*
> *"Você resolve com os agentes, com base em engenharia."*
>
> **Consequências operacionais, em vigor:**
>
> 1. **Lacuna se investiga ANTES da implementação e ANTES da aprovação.** Nenhum item do
>    §4.2 vai para a execução em aberto. O plano só é submetido quando todos fecharem.
> 2. **"Não verificado" nunca é uma seção onde coisas descansam.** É uma fila de trabalho com
>    um agente atribuído e uma prova esperada. §4.2 nomeia quem fecha cada uma e com o quê.
> 3. **"Não dá para medir" é resposta proibida** enquanto houver rota de engenharia: criar a
>    ferramenta, o gate, a sonda, o snapshot ou o parser é parte do trabalho, não um pedido.
> 4. **Nenhuma decisão volta para o dono**, inclusive disfarçada de "registrar como DEC",
>    "confirmar antes de prosseguir" ou "opção (a) ou (b)". Ambiguidade se resolve pela rota
>    mais conservadora **que ainda entrega**, com a suposição escrita no commit.
> 5. **Achado de agente é alegação até verificação própria no disco** — e entra no plano
>    com a evidência, corrigindo o que contradisser. Nesta sessão dois números meus foram
>    derrubados assim (§1.3, §1.4); ficaram os dos agentes, com o método anexado.
> 6. **Dado truncado ou parcial se re-investiga**, nunca se publica como se fosse completo.
>    Amostra se declara "N de M"; estimativa se marca como estimativa e se confirma pelo
>    cálculo exato.
> 7. **Sem prazo em dias, semanas ou meses. Sem "fase 1" que espera amanhã.** *"Tire qualquer
>    margem de 1 dia, dias, meses. Você é IA avançada. Isso é trava que não existe para Opus
>    5."* Portão de execução é **prova medida**, não calendário: passou a prova, o passo
>    seguinte abre no mesmo turno. **Os únicos tetos que permanecem têm causa física externa e
>    medida** — o `Crawl-Delay` que o servidor remoto publica, a vazão do modelo em tok/s, o
>    limite de requisições do operador da API. Margem de prudência própria não é teto: é
>    atraso.
>
> O único limite que permanece: não destruir trabalho, não quebrar produção, não fraudar.
> Esses não são decisão — são proibição.
>
> ---
>
> ## REGRA ZERO-B — QUEM EXECUTA, E QUEM ACONSELHA
>
> **Ordem do dono, 2026-09-15.** Vale para esta sessão, para a execução inteira e para toda
> sessão futura deste plano.
>
> | modelo | papel | quando |
> |---|---|---|
> | **Opus 5** | **padrão de execução e de orquestração** | **toda** frente deste plano, todo subagente de trabalho. É o default, não a exceção |
> | **`advisor`** (ferramenta, sem parâmetros) | conselheiro | **OBRIGATÓRIO — para mim E para os agentes.** É o próprio Fable 5.1, **custa menos** que lançar um Fable e recebe o transcript inteiro |
> | **Fable 5.1** (`Agent` com `model: 'fable'`) | refutação adversarial | **só em momento crítico**, porque é **caro**. Antes de algo caro de reverter: publicação em escala, mudança de gate, correção de família, decisão de arquitetura |
> | **Sonnet** | — | **PROIBIDO nesta execução.** *"Sonnet é bem burro para este plano."* Nenhum subagente, nenhuma etapa, nenhum workflow |
>
> **Consequências operacionais:**
>
> 1. **Todo agente lançado leva no prompt a instrução de consultar o `advisor`** antes de
>    concluir, e de registrar o que o conselho mudou. Conselho que não muda nada também se
>    registra.
> 2. **Eu chamo o `advisor` em quatro momentos**, no mínimo: antes de cada frente, ao mudar de
>    abordagem, quando a medição contraria o esperado, e **sempre antes de declarar pronto** —
>    com o entregável já durável no disco.
> 3. **`advisor` antes de Fable, sempre.** Só se recorre ao Fable direto quando o conselho do
>    advisor não bastar e o passo for caro de reverter. Lançar Fable para tarefa que o advisor
>    resolveria é desperdício de dinheiro do dono.
> 4. **Nenhum `model: 'sonnet'` em `Agent`, `Workflow` ou skill.** Onde o default do harness
>    seria Sonnet, declara-se `model: 'opus'` explicitamente.
> 5. **Esta regra supera a política anterior de orquestração** (que previa "Sonnet 5 leve"),
>    com data e motivo, sem apagar o registro anterior.
>
> ---
>
> ## REGRA ZERO-C — É PROIBIDO LIMITAR ESTE PROJETO
>
> **Ordem do dono, 2026-09-15, vinculante nesta sessão, no plano inteiro e em TODOS os
> contratos do repositório:**
>
> *"Deixa explícito no plano e que vai em todo contrato: não ficar limitando o projeto que tá
> crescendo, sendo indexado, sendo citado milhares de vezes e que pode viralizar para IA, porque
> é plataforma inovadora. Você não limita e é proibido de limitar um projeto meu que esteja
> crescendo e pode viralizar em poucos meses."*
>
> **O estado real, medido, que essa ordem protege:**
>
> | fato | número | fonte |
> |---|---|---|
> | requisições na borda | **88.033 / 24 h** | API Cloudflare |
> | bots identificados | **17.325 / 24 h (19,7%)** | API Cloudflare |
> | agentes de IA | **6.921 / 24 h** | API Cloudflare |
> | **citações em respostas geradas** | **~23.000** | painel Bing, Desempenho de IA |
> | páginas públicas indexadas | **11.106** | `published_manifest` |
> | vetores semânticos servidos por MCP | **11.248** | `internal/semantica` |
> | nós e arestas do grafo jurídico | **79.706 / 393.081** | `grafo_vizinhanca.jsonl` |
>
> **A plataforma está crescendo, indexada e citada. O papel da engenharia é ACELERAR.**
>
> ### O que fica PROIBIDO, e é literal
>
> 1. **Proibido apresentar número de camada inferior como teto do projeto.** Origem é piso, não
>    volume (regra 15). Série cumulativa não se soma. Amostra não é população.
> 2. **Proibido descontar fato por estágio de produto.** "Preview", "beta", "público em teste"
>    descrevem a maturidade de uma API — **nunca a confiabilidade de um número que o operador
>    exibe**. As ~23 mil citações são fato da Microsoft, não estimativa nossa.
> 3. **Proibido derivar teto de capacidade a partir do hardware de hoje.** O servidor novo é
>    ~17× mais rápido no decode e 74–130× no prefill (§P12). Desenhar para o notebook velho é
>    desenhar para uma máquina que deixa de existir.
> 4. **Proibido usar cota de terceiro que não seja de publicação como freio de fábrica.**
>    IndexNow limita **anúncio**; sitemap e descoberta continuam.
> 5. **Proibido inventar risco jurídico para travar frente.** Quem alegar cita a norma e o
>    dispositivo. Sem norma citada, a rota segue aberta (regras 9 e 13).
> 6. **Proibido concluir "não vale a pena", "é marginal" ou "não escala" sem medição na fonte
>    com autoridade.** Instrumento que declara a própria limitação é **ordem de trocar de
>    instrumento** (regra 16).
> 7. **Proibido tratar ausência de método documentado como impossibilidade.** Não haver endpoint
>    público é problema de engenharia a resolver — API alternativa, endpoint de painel, export,
>    ferramenta nova. O contrato de máquina já diz: *"falta capacidade? cria-se"*.
>
> ### O que fica OBRIGATÓRIO
>
> - **Toda afirmação de volume declara a camada medida** junto com o número.
> - **Toda recusa de frente vem com a medição que a sustenta** e com a hipótese do que a
>   reverteria.
> - **Todo teto que permanecer no plano nomeia a causa física externa e medida** — o
>   `Crawl-Delay` que o operador remoto publica, a vazão do modelo em tok/s, a cota de
>   requisições da API. Margem de prudência própria **não é teto: é atraso**.
> - **Esta regra vai para o `CLAUDE.md` do repositório** (regra 18 do §P0) e para a tabela de
>   gatilhos do §2, amarrada ao ato: *antes de escrever que algo é pequeno, marginal, inviável
>   ou não vale a pena*.

## Contexto

Ordem inicial: investigar se o cérebro está produtivo, produzindo lixo ou ligado à toa; se
prestar, levar a produção; achar **por que travou** e corrigir cada achado; garantir que
**ele publique sozinho**; documentar o que aproveitar na migração para o servidor novo
(RTX 5060 Ti 16 GB + 32 GB DDR5 + Ryzen 7 9800X3D), valendo para qualquer servidor futuro. *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)*

Ordens acrescentadas durante a investigação, todas de 2026-09-15, todas já incorporadas:
a onda diária não serve como caminho; **nenhum conteúdo fica parado**; **toda área do
Direito entra**; **o DataJud é para destravar** — e o dono registra que ordena isso
repetidamente; **nenhuma decisão volta para ele** e nenhuma revisão de conteúdo é dele;
teto baixo trava a máquina; o cérebro não pode ficar ocioso e tem de se recuperar sozinho;
e o cérebro decide pelo contexto onde o gate erra para os dois lados.

## Veredito

**NÃO desligar. O cérebro é o ativo mais subaproveitado do repositório, e está travado por
defeito de fiação — não de qualidade.**

Ele já está em produção em **seis superfícies — três consumidas e três apenas servidas**
(§13.4d mediu: as ferramentas MCP `grafo`, `impacto`, `contexto_juridico`, `buscar_semantico` e
`ler_pagina` tiveram **zero chamadas externas em 9 dias**); ele **dobra a elegibilidade** do
canal de acórdãos (2.560 → 4.763 candidatos, **+2.203, +86%**, medido pelo próprio Go); e esse
material está parado porque **o gerador que o consome não é chamado por runner nenhum**.

**Mas a fábrica trava por dentro, e essa é a descoberta maior desta investigação.** A passada
exaustiva montou **2.488 páginas de 4.763 candidatos** e matou **1.405 (29,5%) em
`molde_acima_do_limiar`** — com uma régua que **não é a do gate que decide publicação**.

**E ela é estritamente dominada, provado com número:** dos 135 pares que a régua do gerador
recusa, **a régua real aprova 135 de 135**; o inverso é **0**. Sob a régua real, o **máximo da
família inteira é 0,5193** — o limiar de 0,70 **nunca mordeu uma única vez**. A régua do
gerador apaga todos os dígitos antes de comparar, e em página de acórdão o dígito *é* o
conteúdo. **Com ela corrigida, a faixa medida é 2.488 ≤ x ≤ 3.893 páginas.**
Ordem do dono, literal: *"tem conteúdo bom, acórdãos que podem ir para o ar, e os gates
anulam por burrice"*; *"molde em decisões em conteúdo, isso é normal"*; *"ou o gate fica mais
inteligente ou desativa"*. Ele está certo, e o §1.17 mede.

**Duas correções de rota desta sessão, ambas contra mim, ambas confirmadas por dois agentes
independentes:**

1. **O "+11.607 (+213%)" que eu havia escrito estava inflado 5,3×.** Minha replicação em
   Python omitiu o **primeiro** corte de `elegivel` — `procedimental(r.Classe)`
   (`main.go:515`), que barra **49.807 de 60.221 registros (82,7%)** por serem agravo ou
   embargo. O número correto, medido pelo binário com `-seco`, é **+2.203**. O gerador é a
   autoridade; minha replicação não era.
2. **O "100,0000% de âncora" é medição do filtro sobre si mesmo.** `extracao.go:505` descarta
   o não-ancorado *antes* de gravar, então medir o arquivo prova que o filtro rodou, não que
   a atribuição está certa. O que ficava invisível: **1.966 itens descartados** por invenção
   ou erro do modelo, e — o que importa — **15,51% dos itens do modelo com URN têm o número
   do artigo ausente do próprio `texto_citado`** e **19,0% só se apoiam na folga** de
   `NormaAtestadaNoTexto`. **173 páginas** destravadas só por URN do modelo carregam
   atribuição que o trecho não prova — **defeito de qualidade a consertar no produtor, que
   não trava publicação**.

**As duas correções não se anulam — elas separam FATO de JUÍZO, que é exatamente o eixo da
arquitetura nova.** Molde e similaridade são **juízo** e estão travando conteúdo legítimo:
afrouxam-se por medição. Atribuição de citação legal é **fato** e está frouxa demais:
aperta-se. Fazer só um dos dois seria trocar um defeito por outro.

---

# ROTEIRO DE EXECUÇÃO

Ordem por sangramento → prevenção → escala. Cada passo termina com prova medida e commit
na mesma sessão.

| # | Frente | Por que nesta posição | Detalhe |
|---|---|---|---|
| **−1** | **GRAVAR ESTE PLANO NO REPOSITÓRIO E COMMITAR — AÇÃO Nº 1, ANTES DE TUDO** | **Ordem do dono.** O plano vive hoje em `~/.claude/plans/`, fora do repo: não é versionado, não sobrevive a `/clear`, e **já morreu uma vez nesta sessão** (o processo caiu e o limite de sessão matou dois agentes). 152 KB de medição paga não podem depender de um arquivo fora do git. Destino: **`docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`**, commit imediato, **antes** de qualquer outra frente — inclusive antes do CLAUDE.md | §P−1 |
| **0a** | **CRÍTICO — mudar o MODO OPERACIONAL do Claude Code neste repo** | **Classificada como crítica pelo dono.** As regras existiam e as sessões não as seguiram: o defeito é de **arquitetura de instrução**, não de conteúdo. Regra que pode ser imposta não se escreve — implementa-se como hook, gate, skill ou permissão. Só fica no `CLAUDE.md` o que é fato do projeto. **Vem cedo porque as outras 14 frentes são executadas por sessões de Claude Code** | §P0a |
| **0c** | **REESCREVER os contratos sob a política nova, com teste que cobra** | **Mandato expresso do dono**, não emenda: regra com comando em vez de adjetivo, gatilho por ato, teto só com causa física medida. Bloco canônico replicado em `CLAUDE.md`, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md` e nos `docs/`, travado por teste — sem ele, a próxima condensação apaga (BUG-171) | §P0c |
| **0d** | **Gravar o APRENDIZADO no repositório** | Regra sem o caso vira dogma que a próxima sessão relaxa; o caso sem a regra vira anedota. As armadilhas por arquivo, os erros de método, as decisões de política **e o que foi descartado com evidência** — tudo **dentro dos documentos que já existem**, nunca em documento solto. É o que impede agente futuro de ficar cego e repetir o bug | §P0d |
| **0b** | **Atualizar as memórias e o índice `MEMORY.md`** | O `CLAUDE.md` entra em toda sessão; a memória entra por *recall*. São os dois canais que impedem a cegueira de sessão que o dono cobra — e o texto das quatro já está escrito | §P0b |
| **0** | **Atualizar o CLAUDE.md — PRIMEIRO COMMIT DE CONTRATO** | A execução atravessa sessões, e sessão que não tem a regra no contexto **reabre o DataJud e a "revisão humana"**. É a edição mais barata do plano e a única que previne o erro que o dono mais reclama | §P0 |
| **1** | **Estancar o dado corrompido que já está no ar** | **944 páginas com `datePublished` de hoje e 942 com cronologia impossível, servidas agora — e re-datadas a cada onda.** É o único defeito que piora sozinho enquanto o plano é lido | §P1b |
| **2** | Desfazer a corrupção do shfmt e religar os diários | 8 chaves quebradas cegam o gate, partiram a série do ledger e **escondem a causa real** da fonte morta desde 08-29 | §P2 |
| **3** | Destravar a coleta do STJ | Falha em **7 de 7 disparos**; 6 de 10 datasets nunca coletados; corpus congelado desde 09-10 | §P1 |
| **4** | Matar a família dos produtores órfãos | Órfão não só não roda: deixa de receber as correções dos irmãos — e é a causa-raiz do passo 1 | §P3 |
| **5** | **Arquitetura nova de gates: FATO × PUBLICIDADE × JUÍZO** | **1.405 páginas (29,5%) morrem numa régua estritamente dominada** — dos 135 pares que ela recusa, a régua real aprova 135 de 135. Sem isto, o publicador do passo 7 entrega uma fração | §P4 |
| **6** | Fechar a lacuna de atribuição | Contrapartida do passo 5: molde afrouxa, atribuição aperta. 15,51% dos itens do modelo não provam o artigo. **Roda em paralelo à publicação — não a bloqueia** | §P5 |
| **7** | Publicador autônomo do cérebro | É o que faz "publicar sozinho" acontecer, fora da onda diária. **Roda em dois momentos, e a ordem é bloqueante:** (a) **travessia mínima** com os gates atuais e `lane`/`pageType` **já corrigidos** — a L2 do red-team é dura aqui, corrigir atributo servido depois obriga `--ressemear` sobre 2.488 rotas; (b) o **lote** só depois do passo 5 e de um `-seco` de recenseio com a régua certa | §P6 |
| **8** | Destravar o DataJud | Trava sem fundamento legal, contra ordem recorrente do dono. **Dois enforcers**, não um | §P7 |
| **9** | Nenhum conteúdo parado | 4.763 candidatos, **17.616 agravos fundamentados**, 100 propostas, 3.481 páginas com fundamento posterior — **e as duas filas de refino sem consumidor** | §P8 |
| **10** | Independência e auto-recuperação | Duas guardas mudas provadas; com GPU a fila drena depressa e ele dorme | §P9 |
| **11** | Produto do cérebro sob CI | Zero gates leem o que ele produz; e **20 units mascaram exit 1** | §P10 |
| **12** | Canal social | **Não destravar ainda** — critério medível escrito | §P11 |
| **13** | Documento da IA local para a GPU | Migração iminente; bloqueador nominal da placa já identificado | §P12 |

*A frente do CLAUDE.md, que na primeira versão era o passo 13, foi promovida a passo 0: a
execução atravessa sessões, e sessão sem a regra no contexto reabre o DataJud e a "revisão
humana". As regras estão em §P0.*

---

# 1. Achados medidos

Tudo abaixo foi conferido por leitura própria do código ou medição sobre o dado real. Onde
é estimativa, está marcado.

## 1.1 SANGRAMENTO: a coleta do STJ aborta todo dia, e 6 de 10 datasets nunca existiram

`wikijuridica-stj-acordaos-coleta.service` falha com `ExecMainStatus=1`. **Não é mais
inferência: 7 falhas em 7 disparos**, medidas em `data/ops/owner_alerts.jsonl`, que é onde o
`OnFailure` grava — uma entrada `unit-falhou-wikijuridica-stj-acordaos-coleta` **por dia, de
09-09 a 09-15**. Disparos esperados no período: **7** (timer habilitado em 2026-09-08
14:05:16, diário às 09:40 com 20 min de jitter, `Persistent=true`; último disparo 09-15
09:58:12). **Taxa de falha: 100%.**

**Último sucesso comprovado: 2026-09-10T07:32:07Z** (04:32 -03), por linha de reconciliação
`Result=success ActiveState=inactive`.

**Correção de uma premissa minha:** eu havia tratado o último commit que toca `stj-espelhos/`
(`ea559b13`, 09-10 10:18) como prova do último sucesso. **Errado — commit ≠ sucesso.** A unit
grava o cursor **a cada lote**, por desenho, então esse commit carrega a **saída parcial de um
run que falhou**: última gravação 09-10 09:52:51 -03, alerta 11 segundos depois, às 09:53:02.

**Achado próprio, e é um defeito de instrumentação:** **não existe ledger de execução desta
coleta**. Só a falha deixa rastro datável; o sucesso não deixa linha nenhuma — foi por isso
que o "último sucesso" teve de ser extraído de uma mensagem de reconciliação do systemd, e não
de um registro do projeto. Entra no P1 como artefato obrigatório.

Erro:

```
dataset espelhos-de-acordaos-segunda-secao competencia 20240229:
stjacordaos: decodificando o arquivo mensal de espelhos: invalid character '}' after array element
```

Cursor congelado em `2026-09-10T12:52:51Z`. **O combustível do cérebro está cortado**, e o
`OnFailure` dispara diariamente sem ninguém agir.

A unit pede **10 datasets** (`ops/systemd/wikijuridica-stj-acordaos-coleta.service:60`), o
laço de `internal/stjacordaos/coleta.go:105` os percorre **em ordem**, e `:176` **retorna na
primeira falha**. `segunda-secao` é o **3º**:

| # | dataset | estado no cursor |
|---|---|---|
| 1 | terceira-turma | 52 janelas, até 2026-08 |
| 2 | quarta-turma | 52 janelas, até 2026-08 |
| 3 | **segunda-secao** | 21 janelas, para em 2024-01 — **aborta aqui** |
| 4 | **primeira-turma** | **3 janelas** — ~94% ausente |
| 5–10 | segunda-turma, primeira-secao, **corte-especial**, quinta-turma, sexta-turma, terceira-secao | **NUNCA COLETADOS** |

Entre os ausentes: a **Corte Especial** (maior autoridade do STJ), **Primeira e Segunda
Turmas e Primeira Seção** (tributário, público, previdenciário) e **Quinta e Sexta Turmas e
Terceira Seção** (matéria criminal inteira).

### O que o censo da fonte mediu — e três correções a números meus

| afirmação anterior | medido |
|---|---|
| "6 datasets ausentes com 44/48/51/62 recursos" | **todos os 10 têm 52 recursos mensais** (segunda-turma: 51), cobrindo `20220531`–`20260831` |
| "lacuna de ~9 meses em 6 datasets" | **391 competências** |
| "amostra por stride fecha o volume" | **não fecha**: dispersão mensal de bytes com **CV de 101–125%**; contra as duas séries totalmente conhecidas, stride-4 erra até **±27%** e stride-6 até **±59%** — nada melhor que a banda de ±30% que eu já tinha. Por isso o método virou **censo `HEAD` completo** |
| "usar a API do CKAN" | **proibida**: `robots.txt` do STJ traz `Disallow: /api/`. Os tamanhos saem da página HTML mais `HEAD` nas URLs de download |

**Confirmados de forma independente:** as **7 falhas em 7 disparos** (por `owner_alerts.jsonl`,
09-09 a 09-15 — o journal só retém o boot corrente) e o alinhamento do parser, agora **99 de
99** exatos por `content-disposition` (antes 21/21).

### O corpus pós-recuperação, agora medido: 165.981 acórdãos — e meu "~210.000" estava 26% alto

**Censo integral, não amostra:** 391 requisições `HEAD`, uma por competência, **zero falhas**.

| dataset | recursos | MiB | reg/MiB | acórdãos novos |
|---|---|---|---|---|
| quinta-turma | 52 | 124,920 | 276,1 | **34.492** |
| sexta-turma | 52 | 86,155 | 344,9 | 29.715 |
| segunda-turma | 51 | 62,854 | 290,0 | 18.226 |
| primeira-turma | 49 | 33,958 | 362,8 | 12.320 |
| primeira-secao | 52 | 17,152 | 231,5 | 3.971 |
| **corte-especial** | 52 | 12,869 | **282,4 — contado** | **3.634** |
| terceira-secao | 52 | 7,127 | 236,8 | 1.688 |
| segunda-secao | 31 | 5,172 | 331,3 | 1.714 |
| **total** | **391** | **350,2 MiB** | | **105.760** |

**Corpus final: 60.221 + 105.760 = 165.981** (banda **154.747–172.721**). Custo: **350,2 MiB e
78,5 min** impostos pelo `Crawl-Delay` do STJ — **4 disparos do timer diário**.

**Por que a amostragem foi abandonada, com número:** o volume mensal tem **CV de 101–125%**;
testados contra as duas séries 100% conhecidas, stride-4 erra até **+27%** e stride-6 até
**+59%** — igual ou pior que os ±30% que eu já tinha. **Censo custou menos que confiar em
amostra.**

**A razão varia muito mais por órgão do que o disco sugeria: 220,9 a 347,8 reg/MiB.**
Transportar a média global de 324,78 teria **superestimado a Primeira Seção em 47%**.

> **E o controle de ~68 acórdãos/mês da Corte Especial estava certo — o instrumento é que
> estava errado.** Com a razão transportada, a projeção deu 80,4/mês (+18%). O agente **baixou
> as 52 competências e contou: 69,9/mês (+2,8%)**. Sem esse controle, o mesmo viés teria ido
> para os seis datasets ausentes. *(É a lição do §regra 19 outra vez: medir em vez de calibrar
> contra a própria expectativa.)*

### A elegibilidade projetada linearmente erraria por 36–49%

| | projeção linear | **por dataset, medido** |
|---|---|---|
| candidatos | 7.056 | **4.485** (IC 4.003–5.150) |
| páginas | 6.857 | **3.496** |

**A causa é uma variação de 38× entre órgãos: 0,35% de candidatos na Quinta Turma contra 13,44%
na Primeira Seção.** O motivo é estrutural e não estatístico: **o habeas corpus chega como
`AgRg no HC`** — 51,5% da Quinta Turma — e `AGRG` está no filtro `procedimental`. **A Quinta
Turma traz 33% dos acórdãos novos e apenas 6% dos candidatos.** *(A réplica de `elegivel()` foi
calibrada contra o binário e reproduz 2.560 e 4.763 exatos.)*

**Nota de método:** o número de páginas continua projeção linear — o rendimento anti-molde de
61,0% é **sequencial** e só se resolve rodando o gerador, que é escrita e ficou fora do encargo.

### ACHADO QUE MUDA A ESCALA: 1,95 GiB de acervo histórico, ~5,6× o corpus inteiro

O `20220508.zip` de cada dataset não é um arquivo antigo qualquer. Lendo o **central directory
por `Range`** — 2,5 MiB em vez de baixar 439,6 —, medido:

- **1.953,7 MiB descomprimidos**
- baldes desde **`20001231.json`**
- **613.000 a 679.000 acórdãos**
- **~5,6× todo o corpus pós-recuperação**
- mesma licença **CC-BY**

**A única coisa que separa o projeto desse acervo é a regex `\d{8}\.json` em
`internal/stjacordaos/dataset.go:33`.** Vinte e dois anos de jurisprudência do STJ, a uma linha
de distância. *(Fora da conta dos 165.981, de propósito — é frente própria dentro do P1.)*

### ACHADO GRAVE: a fonte serve arquivo de outro órgão, e o coletor não percebe

`quinta-turma` e `sexta-turma`, competências `20260131` e `20260228`, devolvem arquivos
**byte-idênticos (mesmo `sha256`) cujo conteúdo é da PRIMEIRA TURMA**. **O coletor não valida
órgão julgador contra o dataset** — gravaria **38 acórdãos triplicados**, com o órgão errado, e
nada acusaria.

*Escopo honesto: 78 de 78 outros arquivos baixados estão coerentes; 5 competências da janela
rala da Quinta Turma não foram baixadas nem verificadas.*

**Correção, junto com a do `return`:** guarda `nomeOrgaoJulgador` × slug do dataset, com **4
fixtures verificadas por hash**. E a fixture do defeito original também está pronta:
`segunda-secao 20240229`, **599 bytes** — único abaixo de 10 KB junto com outros dois.

### AÇÃO IMEDIATA: 62 MB de censo estão em `/tmp`

O resultado do censo está em `/tmp/stj-census/` e **custa ~80 min de `Crawl-Delay` para
refazer**. O contrato de máquina é explícito: *"produto nunca mora em `/tmp`: some no reboot"*.
**Mover para dentro do repositório, versionado, no commit do §P−1** — antes de qualquer reboot.

*(O número comprimido — ~439,6 MiB nos 10 datasets, sendo 110 MiB só na Quinta Turma — era o que
eu tinha antes. O que importa é o descomprimido, medido pelo central directory: **1.953,7
MiB**.)*

### A elegibilidade por órgão, com replicação CALIBRADA

A réplica de `elegivel()` foi calibrada contra as duas medições autoritativas e **reproduz
2.560 e 4.763 exatamente** — então o recorte por órgão é medido, não chutado:

- **a taxa de candidato varia 4,5× entre órgãos** (de **1,39%** a **6,32%**), e decompõe-se em
  uma parcela procedimental (80,0–95,9%, o termo dominante) vezes um rendimento condicional
  bem mais estável;
- **81,4% da sobreposição da IA vem do PARSER, não do modelo** — ou seja, o ganho "com IA" é
  majoritariamente **barato de reproduzir** sobre os registros novos, sem GPU;
- Corte Especial com censo completo (52/52, 12.869 MiB) projeta **77,6–86,1 acórdãos/mês**
  contra o controle de ~68 — divergência que está sendo fechada **baixando os 52 arquivos
  (12,9 MiB)**, e não ajustando a razão para caber no controle. *(É o método certo: medir em vez
  de calibrar contra a própria expectativa.)*

**Diagnóstico fechado — é malformação do upstream, não truncamento nosso.** Baixado com
`internal/wikijuridicabot` e `Crawl-Delay: 10` respeitado: HTTP 200, **599 bytes**, sem
`Content-Encoding`, sha256 `ea2537c36c1e…`. **599 bytes contra teto de 64 MiB — 112.000×
menor.** O arquivo é um objeto-sentinela de mês vazio escrito à mão
(`"Obs": "Sem lançamentos para o mês de fevereiro/2024"`) com **duas chaves fechando um
objeto só** — o `}` sobrando é o 4º byte a contar do fim. Erro de digitação do publicador.

Taxa-base de malformação medida: **1 em 129 ≈ 0,8%** (único arquivo abaixo de 30 KB em 52
meses da série, mais os 128 lotes já parseados).

O *fail-closed* de `ParseEspelhos` (`espelho.go:42-48`) está **certo** e não se toca — lista
vazia seria indistinguível de "o mês não teve acórdão". O defeito é de **orquestração**.

## 1.2 A CAUSA DO TRAVAMENTO: produtor órfão, e é uma família

`tools/run-daily-content` publica sozinho todo dia, pelos geradores do mapa `GERADORES` (5
entradas). **Nenhum dos dois motores que consomem o cérebro está nele:**

| Motor | Estado | Consequência |
|---|---|---|
| `cmd/generate-acordao-pages` | commitado em `45d33ee8`, **em runner nenhum** | shard `stj-acordao-derivado-01.jsonl` **nunca existiu** |
| `cmd/generate-lei-artigo-pages` | **em runner nenhum** | rodou **uma vez à mão** em 2026-09-10 (38 páginas, publicadas) e nunca mais |

As únicas ocorrências fora do próprio código são **comentários** (confirmei que a única em
`tools/test_generate_motor_tier_a.py:308` é docstring, não invocação).

**Ser órfão custa duas coisas, e a segunda é a cara:** o motor deixou de receber as
correções dos irmãos. `grep -rln tetodelote cmd/` devolve exatamente os **cinco** geradores
da onda e **nenhum** dos dois do cérebro. Mesma assimetria no limiar anti-molde (cinco em
0,60 alinhados ao gate; os órfãos em 0,70 sobre outro corpo). **Código que não roda não
aparece em incidente, e por isso não é consertado.**

Precedente idêntico já vivido: `tools/run-daily-content:446` descreve
`cmd/generate-writeback-extracoes` como *"PRODUTOR ÓRFÃO, medido em 2026-09-10"* — corrigido
virando a etapa 1.5/9 da onda.

Órfãos vivos hoje: os dois motores, `tools/generate-propostas-reescrita` e
`tools/generate-first-published-at`.

## 1.3 O ouro parado: +2.203 acórdãos elegíveis, medidos pelo próprio Go

**Medição autoritativa** — não replicação minha, e sim o binário:

```
./tools/go-modern run ./cmd/generate-acordao-pages -raiz /opt/wiki -seco -limite 30
corpus: 60221 acórdãos lidos, 4763 candidatos de mérito com evidência suficiente
recusas: agravo_ou_embargo_nao_vira_pagina_propria 49807
         ementa_curta_demais_para_duas_camadas       4500
         sem_ancora_legal_substantiva                1151
```

| cenário | candidatos |
|---|---|
| só fonte oficial | **2.560** |
| com a sobreposição do cérebro | **4.763** |
| **destravados pelo cérebro** | **+2.203 (+86%)** |

**A IA local quase dobra a elegibilidade do canal.** Ela move exatamente um corte —
`sem_ancora_legal_substantiva`, de 3.354 para 1.151. Origem das 2.203: **parser 1.400**,
modelo `qwen3.5:4b` **803**; 283 só por súmula; 762 só por URN do modelo.

**Correção de um erro meu, de 5,3×.** Eu havia escrito 5.462 / 17.069 / +11.607. Dois
agentes independentes reproduziram **exatamente** esses três números **com o meu filtro** — e
foi isso que provou o erro: minha replicação aplicava 3 dos 6 cortes de `elegivel`
(`main.go:514-543`) e **omitia o primeiro**, `procedimental(r.Classe)` (`:515`), que barra
**49.807 registros (82,7%)** por radical AGINT/AGRG/AGREG/EDCL/ARESP/EARESP/EDV/AGRESP.
Também omitia `TipoDecisao == "ACÓRDÃO"` (`:518`) e `stjacordaos.MotivoBarrado` (`:525`) —
ambos com 0 reprovações hoje, mas vivos no código.

*Controle de ordem de grandeza que fecha:* o commit que criou o gerador (`45d33ee8`) mediu
**1.674 elegíveis em 37.085 linhas = 4,51%**; a medição de hoje dá **2.560 em 60.221 =
4,25%**. Meus 5.462 seriam **9,1%** — incompatível com a única passada real registrada.
**Lição de método, que vira regra:** quando a replicação bate com o esperado, isso é motivo
para desconfiar dela, não para confiar. O binário é a autoridade.

### Teto estrutural, e o que ele significa

O overlay do cérebro **só** move `sem_ancora`. Agravo (49.807) e ementa curta (4.500) são
intocáveis por extração. Teto com extração perfeita: **4.763 + 1.151 = 5.914** candidatos —
dos 3.354 possíveis, **2.203 já estão realizados (65,7%)**.

### Candidato ≠ página — e a passada EXAUSTIVA já foi feita

`-seco -limite 5000` **exauriu o poço** (12 min 15 s de parede). Prova de exaustão, que fecha
na aritmética: 2.488 + 1.405 + 682 + 165 + 22 + 1 = **4.763**.

| | |
|---|---|
| candidatos | **4.763** |
| **páginas montadas** | **2.488** |
| `molde_acima_do_limiar` | **1.405 (29,5%)** ← a régua errada |
| `ementa_sem_item_transcritivel` | 682 |
| `citacao_abaixo_do_minimo_oficial` | 165 |
| `camada_autoral_nao_deixa_espaco` | 22 |
| `rota_duplicada_no_corpus` | 1 |

**REVERSÃO: os 39,7% eram PISO, não teto.** Eu havia escrito que o rendimento cairia com a
profundidade, porque o gerador ordena por evidência e o anti-molde endurece à medida que
aceita. **Medido, acontece o contrário:** 39,7% → 42,3% → **52,2%**. Por segmento do poço:
**39,7% → 45,2% → 62,1%** — a cauda rende **mais** que a fatia rica.

**Por quê:** `molde_acima_do_limiar` é *front-loaded* (42,2% → 41,7% → 17,2%) — a fatia rica
compartilha as âncoras legais de alta frequência, e é justamente ali que a régua errada mais
morde. `ementa_sem_item_transcritivel` é *back-loaded* (6,7% → 20,1%). **São defeitos
diferentes em pontas diferentes do poço**, e o mais caro é o que ataca o material melhor.

**Com a régua corrigida (§1.17), a faixa medida é 2.488 ≤ x ≤ 3.893 páginas.** Atribuível à
IA local: piso **~875**, ponto **~1.151**, teto **~1.251** *(derivado — não há flag para rodar
sem a sobreposição; `main.go:184-187` só expõe `-raiz`, `-limite` e `-seco`)*.

**2.488 montadas ≠ 2.488 publicáveis:** a cadeia do §5 não rodou sobre elas. É o que a prova
de travessia do P6 mede.

`sem_duas_fontes_oficiais_verificaveis`: **0** (o `manifest.jsonl` cobre os 128 `fonte_url`).
`rota_ja_publicada` contra os 11.206 intents dos outros shards: **0**.

*Nota sobre o custo:* `main_test.go:583-589` avisava que o Jaccard O(n²) não terminaria 1.569
páginas em 10 min. **O aviso fica superado no fato** — a passada exaustiva terminou —, **mas
não no desenho**: numa passada real o shard alimenta `previas` e passam a rodar dois laços por
candidato (~×2,1). A rotação de shard do P6 existe para isso.

**Os 49.807 agravos e embargos não são descarte — são pauta**, pelo §1.15. Agravo interno e
embargo de declaração são decisões judiciais reais. Eles não viram página **própria** porque
não têm mérito autônomo; a rota para eles é agregação (por tese, por dispositivo, por
relator) e está no P7.

E o poço cresce: só **43.507 dos 60.221** foram extraídos — e o arquivo cresceu **três vezes
durante a auditoria** (43.492 → 43.504 → 43.507). O cérebro está apendando ao vivo.

**Nota de reprodutibilidade, que vira regra de operação:** `data/ai/extracoes_dispositivos.jsonl`
e `data/ai/dispositivos_promovidos.jsonl` estão `M` no `git status` e mudam durante a
medição. **Toda medição sobre o produto do cérebro exige snapshot datado** (hash + linha de
corte), senão nenhum número é reproduzível.

## 1.4 A âncora literal fecha em 100% — e esse número não mede o que eu disse que media

**O que a âncora prova:** o trecho citado existe literalmente no texto-fonte. Conferido com a
normalização exata de `extracao.go:383` sobre `ementa[:3000]` — que é **o que o modelo de
fato leu** (`cmd/cerebro/main.go:766`, cortado em `TetoCharsExtracao`, `extracao.go:49`):
**126.601 / 126.601**, e `texto_sha256` bate em 41.420/41.420. **Nenhum trecho inventado.**

**O que ela NÃO prova, e eu apresentei como se provasse:**

1. **É medição do filtro sobre si mesmo.** `extracao.go:505` descarta o não-ancorado *antes*
   de gravar. Medir o arquivo prova que o filtro rodou.
2. **O denominador estava inflado, e o RÓTULO da grandeza estava trocado.** 135.181 é a soma
   de todos os **ITENS** de um arquivo append-only — eu havia escrito "todas as linhas".
   Medido em 2026-09-16: o arquivo tem **45.076 linhas e 138.555 itens**; no git ele vai de 660
   a 37.176 linhas em HEAD. **Nunca teve 135 mil linhas.** Última por `(chave, modelo)` — que é
   a chave do cache, `extracao.go:870` — dá **126.601** (recontado hoje: 129.837); última por
   `chave`, **105.263** (hoje 105.766). A conclusão não muda; o nome da grandeza estava errado,
   e grandeza com nome errado é exatamente o que a regra 19 manda corrigir na mesma sessão.
3. **Minha conferência era mais frouxa que o filtro.** Conferi contra ementa + dispositivo +
   inteiro teor + jurisprudência citada — superconjunto do que o modelo leu.
4. **A taxa de invenção ficava invisível.** Somados: `descartados` 1.482 +
   `descartados_precedentes` 91 + `descartados_norma_nao_atestada` 380 +
   `descartados_geracao_ambigua` 13 = **1.966 itens que o modelo inventou ou errou**. O filtro
   os pegou — e é exatamente por isso que ele fica.

### A atribuição, medida pela primeira vez — e é aqui que mora o risco P1

Separando itens do modelo (13.733) dos do parser (112.868 — o parser atribui por construção,
do mesmo `match`), sobre os itens do modelo com URN LexML:

| medida | valor |
|---|---|
| número do artigo **ausente** do próprio `texto_citado` | **1.709 / 11.022 = 15,51%** |
| norma atestada **dentro** do trecho | 9.156 / 11.308 = 81,0% |
| norma que **só se apoia na folga** de `NormaAtestadaNoTexto` | **2.152 = 19,0%** |
| norma ausente **em qualquer lugar** | **0** — o filtro segura para URN LexML |
| **nem artigo nem norma no trecho** | **1.476 = 13,1%** |

Maiores ofensores do artigo fora do trecho: **CPC/2015 770, Código Civil 186, Código de
Processo Civil 147**. Exemplo real, acórdão `000812565`: `art. 1.021, § 4º` do CPC atribuído a
um trecho que fala da **Súmula 282** — o trecho não sustenta a atribuição.

**O cruzamento que fecha a gravidade:** das 762 páginas destravadas **só** por URN do modelo,
**225 carregam ao menos uma URN cuja norma só se atesta fora do trecho**, e **173 uma em que
nem artigo nem norma aparecem no trecho**.

**Enquadramento corrigido:** isto é **defeito de qualidade**, não risco disciplinar. O
Provimento 205/2021 alcança publicidade e captação, não precisão de citação em conteúdo
informativo. Conserta-se porque conteúdo errado é ruim para o leitor — e **sem travar a
publicação** (P5).

**Achado lateral, baixo mas real:** **267 URNs promovidas sem `!art`** (ex.:
`urn:lex:br:federal:lei:2015-03-16;13105`). `admissibilidade` (`main.go:380-387`) não casa
numa URN nua e devolve `false`, então uma URN do CPC que pode ser o art. 1.022 conta como
**substantiva**. **79 acórdãos passam a âncora só por isso.** E `reURNArtigo` (`:1025`) também
exige `!art`, então essas URNs não geram bloco de dispositivos nem fonte de norma — elegem a
página e não a abastecem.

**O que continua verdadeiro e é o motivo de o cérebro ficar:** o modelo acrescenta valor real
— nas 6.391 linhas em que o LLM rodou, 30.177 dispositivos contra 15.317 do parser
(**+14.860**, delta > 0 em 84,8% das linhas) — e é indispensável porque **70,2% dos acórdãos
(42.291) chegam da fonte sem nenhum dado estruturado**. O defeito é de **atribuição**, não de
invenção, e atribuição se conserta com regra determinística (P6), não trocando de modelo.

**Suspeita levantada e retirada com medição:** as 738 linhas legadas (anteriores ao filtro de
2026-09-10, sem `versao_do_prompt`) geram 720 promoções e 14 páginas destravadas. Para URN
LexML: **0 não atestadas**. Das 987 súmulas nessas linhas, 910 atestadas por regex; as 77
restantes são enumerações ("Súmulas 7 e 83 do STJ") que a regex de conferência não parseia, e
os 4 exemplos amostrados aparecem no próprio trecho. **Sem evidência de invenção.**

## 1.5 O cérebro já está em produção, em seis superfícies — três consumidas, três só servidas

> **CORREÇÃO desta seção, medida em §13.4d.** Eu listei as seis como se todas fossem consumo.
> **Não são.** Em 9 dias de `mcp_method` gravado houve **301 `tools/call`, 245 deles (81,4%)
> das nossas próprias sondas**, e as cinco ferramentas de ativo — `grafo`, `impacto`,
> `contexto_juridico`, `buscar_semantico`, `ler_pagina` — receberam **zero chamadas externas**.
> Os 56 externos são **censos de diretório MCP** (`SaSame-MCP-Audit/0.1` sozinho é 50%), não
> assistente de consumidor. **Superfície servida não é superfície consumida**, e a consequência
> de engenharia está no §13.4: os ativos do cérebro têm de sair do MCP e entrar no **HTML**, que
> é o que a classe que cita de fato lê (128× mais que a gêmea).

| Superfície | Artefato | Prova |
|---|---|---|
| `public/datasets/extracoes-dispositivos-*.jsonl.gz` | extrações | 3,55 MB; cresce todo dia (3,26 → 3,41 → 3,55 em 3 dias) |
| `public/datasets/grafo-juridico-{nos,arestas}-*.jsonl.gz` | grafo | 35 MB + 8 MB por dia |
| HTML público das páginas `leis-motor` | `dispositivos_promovidos` | 38 intents, **38 publicadas** |
| MCP `buscar_semantico` | embeddings | **11.248 vetores**, dim 1024; **0 páginas publicadas sem vetor** |
| MCP `grafo`, `impacto`, `contexto_juridico` | `grafo_vizinhanca.jsonl` | 79.706 nós, 393.081 arestas |
| MCP `contexto_juridico` → `risco_de_superacao` | `risco_superacao.jsonl` | 4.986 páginas, 3.481 com risco |

**104.002 das 393.081 arestas do grafo (26,5%) vêm das extrações.** O grafo se regenera do
disco em 43 s sem LLM — mas é **irreproduzível do zero sem ele**.

**Nota de fato técnico, que NÃO é argumento a favor de nada:** desligar o Ollama remove
`buscar_semantico` de `tools/list` no próximo restart — `internal/httpserver/mcp_semantico.go:79-88`
só anuncia a ferramenta se o Ollama responder em 3 s no boot. **Isto deixou de servir como
motivo para manter o cérebro:** a ferramenta teve **8 chamadas em 9 dias, todas nossas**. O
motivo de manter o cérebro são as **+2.203 páginas elegíveis** e as 104.002 arestas do grafo,
não uma ferramenta que ninguém de fora chama.

Isso importa porque o tráfego de agente é real: `data/ops/ai_citation_signal_daily.jsonl`
soma **93.727 requisições de agentes de IA em 36 dias**, **40.220 com
`is_citation_interest`** (Amazonbot 36.832, PerplexityBot 20.752, meta-externalagent
15.302, oai-searchbot 4.296).

## 1.6 A onda diária entrega 1,4% da capacidade declarada

| medida | valor |
|---|---|
| execuções com zero falhas | **3 de 44** (6,8%), todas do mesmo dia 08-26 |
| execuções consecutivas sem verde desde 08-27 | **≥ 30** (última linha `resultado: "ok"` é 08-26; depois dela, 30 linhas, todas `parcial`. É **piso**: execução barrada pela trava não grava linha — defeito (a)) |
| crescimento medido do manifesto | **11.039 → 11.106 = +67 em 5 dias** (commit `315ac61b` de 09-10 até hoje) |
| páginas de **uma** execução manual em 09-09 | **898** |
| teto declarado dos 5 geradores | 410/dia → entrega real **1,4%** |
| execuções recentes que entregaram zero intents | **5 de 10** |
| alerta `onda-diaria` em `owner_alerts.jsonl` | **35 aberturas, 3 resoluções**, aberto desde 08-27 |
| estoque gerado e não publicado | **100** — exatamente os 100 críticos |

O último número é o diagnóstico: **a esteira de publicação está drenada e correta; falta
oferta.** As 5 fontes do mapa respondem 304/inalterada/TLS-failure, enquanto **o único canal
com matéria-prima viva — a extração do cérebro — não está ligado a gerador nenhum**. E a
mesma esteira provou aguentar 6× o volume mensal numa tarde.

## 1.7 Um commit de estilo quebrou a onda em silêncio

`d4c942f2` (2026-09-11, *"style(shell): 108 scripts formatados pelo shfmt, com bash -n antes
e depois"*) espaçou o hífen dentro das chaves dos arrays associativos. O shfmt lê
`[stj-precedentes]` como expressão aritmética. `bash -n` aprova — é sintaticamente válido.

8 chaves corrompidas (`tools/run-daily-content:337,338,345,346,347,369,370,371`):

```bash
[noticias - oficiais]="./cmd/collect-noticias-oficiais -limite 200"
```

Reproduzi em bash isolado: contra o filtro `[ "$chave" = "noticias-oficiais" ]` (`:355`),
**0 chaves casam**. Efeitos:

1. **A passada das 12:20 deixou de coletar** — o filtro desliga TODOS os coletores.
2. **`tools/check-frescor-canal-diario` ficou cego** — casa fontes por string exata
   (`:68-85`), lê `{}` para 4 dos 5 canais e passa a julgar o último registro hifenizado,
   de **2026-09-10**. O gate acusa hoje *"diarios — 0 de 166 coletada(s), marca d'água
   2026-08-29"* enquanto o log real diz `tls: handshake failure`. **Há 5 dias o alerta
   nomeia a causa errada.**

Varredura confirmou: corrupção **contida a este arquivo**.

## 1.8 Duas guardas do cérebro estão mudas — as duas provadas

**(a) O `flock` nunca guardou nada.** `saude.go:87` usa
`/tmp/opt-wiki-agent-heavy.lock`; `carga_linux.go:18` abre com **`os.O_CREATE`**; a unit tem
**`PrivateTmp=true`** (`wikijuridica-cerebro.service:72`). O daemon **cria o próprio lock no
seu `/tmp` privado**, tranca esse, e conclui sempre "não tomado".

Prova empírica — dois arquivos distintos:

```
/tmp/opt-wiki-agent-heavy.lock                  criado 2026-09-10 17:05  (host)
/proc/926445/root/tmp/opt-wiki-agent-heavy.lock criado 2026-09-14 04:40  (daemon)
namespaces de mount:  4026532461  ×  4026531841
```

O arquivo do daemon nasceu **no minuto em que a unit subiu**. Em 10 dias o cérebro pausou
**uma única vez**, e por `loadavg 28,28` — a assinatura de um build pesado, que é
exatamente o que o lock existia para pegar *antes*.

**(b) O alerta do cérebro nunca pode disparar.** Medido com `systemctl show`:

```
Restart=always  RestartUSec=15s  StartLimitIntervalUSec=10s  StartLimitBurst=5
WatchdogUSec=0  NRestarts=1
```

Cinco partidas a 15 s levam **no mínimo 60 s**; a janela é de **10 s**. O burst **nunca é
atingido**, a unit **nunca** entra em `failed`, e o `OnFailure=wikijuridica-alerta@%N` que
ela declara **nunca dispara**.

**Refinamento medido, e ele torna o defeito invisível ao grep:** os `10s`/`5` **não são
declarados na unit** — são `DefaultStartLimitIntervalUSec` e `DefaultStartLimitBurst` do
*manager*. A unit não tem nenhum `StartLimit*`. **Quem procurar o literal
`StartLimitIntervalSec=0` não acha o defeito.** E a pergunta sobre reset do contador é
irrelevante: com `RestartSec=15`, **nenhuma janela de 10 s contém duas partidas**, então o
burst de 5 é inalcançável sob qualquer semântica. `OnFailure` só existe a partir de `failed`
(`man systemd.unit`).

**`StartLimitIntervalSec` é diretiva de `[Unit]`** — em `[Service]` é ignorada **em
silêncio**. O próprio repositório já pagou por isso:
`ops/systemd/wikijuridica-social.service:84` registra que *"só `systemctl show` revelou"*.

**Prior art que fecha as saídas.** A docstring de `tools/check-units-alarme:84-106` mediu
neste mesmo systemd 252 as quatro classes de alarme: **(A) restart em laço NÃO dispara** — 87
restarts na rede social, em produção, sem alerta; (C) `Requires=` dispara; (D) socket dispara.
O cérebro usa `Wants=ollama.service` e não tem socket ⇒ **(C) e (D) estão fechadas. Sobra só
a (A), que é a que não dispara.**

**E não há detector.** `check-units-alarme` isenta daemons por estrutura; a derivada de
`NRestarts` em `tools/check-portal-health` cobre `wikijuridica-server{.service,.socket}` e
`wikijuridica-social` — **não o cérebro** (`grep -c cerebro tools/check-portal-health` = 0).

Somado a `cmd/cerebro/main.go:157-160` + `os.Exit(1)` (`:81`): **Ollama fora do ar no boot =
laço eterno e mudo, ~4 partidas por minuto**, visível só num journal que guarda um boot. Com
`WatchdogUSec=0`, worker **travado** também é invisível — fica `active (running)` para sempre.

Somado a `cmd/cerebro/main.go:157-160`, que sai com erro se o Ollama não responder **no
boot**: **Ollama fora do ar quando o cérebro sobe = laço de reinício eterno e mudo.**
`WatchdogUSec=0` fecha o quadro: processo travado fica `active (running)` para sempre.

## 1.9 A atribuição não é atestada — o risco que sobra

A âncora cobre `texto_citado` e `norma`. **O campo `artigo` não tem âncora nenhuma** — o
trecho pode ocorrer no texto e a URN apontar outro dispositivo. O próprio repositório admite
em `tools/check-extracao-por-parser-amostra`: *"a âncora é literal e a URN é validada pelo
lexml, mas nada disso mede ATRIBUIÇÃO"*.

Dois buracos da mesma classe:
- **Não há catálogo de súmulas.** `sumula:STJ:5` é aceita porque o texto diz isso; nada
  confere se existe. Súmulas contornam o `internal/lexml` inteiro (`extracao.go:726`).
- Para norma numerada, `NormaAtestadaNoTexto` testa o número **em qualquer lugar do texto**,
  não dentro do `texto_citado` (`triagem.go:224`).

**Isto é defeito de QUALIDADE, e o enquadramento importa** (fundamento conferido em fonte primária: `docs/goal/JURIDICO_BASE.md` §1.4, que também escopa o EAOAB art. 34, XIV — *"deturpar o teor de dispositivo de lei para confundir o adversário ou iludir o juiz"* —, norma **processual e dolosa**, que não alcança verbete).** Eu havia classificado atribuição
imprecisa como *"P1 permanente sob a OAB"*. Falso: o Provimento 205/2021 e o **CED arts. 39 a 47-A**
alcançam publicidade e captação, não precisão de citação em conteúdo informativo. **Conserta-se
porque conteúdo errado é ruim para quem lê** — e a plataforma vive de ser confiável para leitor
humano e para agente de IA —, **não porque alguém pune. E não trava publicação** (P5).

## 1.10 Zero cobertura de CI sobre o produto do cérebro

- **Nenhum gate em `internal/checks/*.go`** lê `extracoes_dispositivos.jsonl` ou
  `dispositivos_promovidos.jsonl`.
- Dos 5 checks Python que cobrem a extração, **4 não estão em runner nenhum**. Só
  `check-writeback-do-cerebro-nao-atrasa` está na bancada diária — que roda em **rodízio
  orçado** (`gates_registrados: 358`, `gates_executados: 138`) e cuja unit declara
  `SuccessExitStatus=1`, ou seja, **vermelho ali não alerta ninguém**.

A qualidade de hoje é real, mas **não é guardada por nada automático**.

## 1.11 Um filtro conservador deixa 17.691 acórdãos fora da fila

Medido: 7.636 extraídos pelo worker, 34.852 pendentes, **17.733 sem tarefa nenhuma**
(soma = 60.221). Desses, **17.691 não têm extração nem do parser offline — estão
intocados**.

Causa: `enfileirarExtracoes` em `cmd/cerebro/main.go` tem
`soSem := fs.Bool("so-sem-referencias", true, ...)` — **default `true`**. Só entram acórdãos
sem `dispositivos_citados_urn` e sem `sumulas_citadas`.

**A premissa nunca foi testada.** Sobre os 17.930 com dado estruturado, a fonte lista
**mediana de 2** itens, enquanto o texto menciona `art.` ou `súmula` mais vezes em **12.160
deles (67,8%)**. Menção não é dispositivo — é **limite superior, não medida** — mas basta
para medir, e medir custa zero: o parser tem 100% de âncora e não usa LLM. Estimativa de
ganho direto: até **1.478 páginas** a mais, entre os 1.538 acórdãos hoje recusados por
`sem_ancora_legal_substantiva` que estão nesse grupo e cujo texto tem sinal de norma.

*Correção de rota:* o enfileiramento automático **não** se limita a embeddings —
`tools/run-cerebro-enfileirar:34` chama `enfileirar-extracoes`, e o `.path` observa
`content/pages.json` **e** o manifesto do STJ. A lacuna é do filtro, não da automação.

## 1.12 Artefatos parados e mortos

| Artefato | Estado |
|---|---|
| `propostas_reescrita.jsonl` | 100 propostas, lote único de 2026-09-08, **zero aplicadas**; gerador **não agendado** e hoje **não termina** |
| `grafo_manifest.json` | 12 KB, **nenhum leitor** fora do teste |
| `comentarios_gerados.jsonl` | 3 peças (1 tema), 1 aprovada, **nenhuma publicada** — é desenho: a unit roda sem `--publicar` |
| `publicacoes_cerebro.jsonl` (DEC-059) | **não existe**: o cérebro nunca publicou em rede social |
| `openai_review_batch_*.jsonl` | 37 MB de junho, resultado **0 bytes** — serviço externo que o contrato proíbe |
| `first_published_at.json` | congelado há 18 dias; **999 páginas** têm a estreia reescrita para "hoje" a cada onda |
| **a fila de refino tem produtor e NÃO tem quem reescreva** | **Correção de duas alegações minhas.** (1) Escrevi "1.267 médios": o real é **10.337**, e (2) escrevi "fila parada desde 09-04": falso para `v2_rewrite_queue.jsonl`, que é **regenerada inteira a cada ingest** — as 3.201 linhas carregam a data da última regeneração (09-11; em HEAD, 3.200 de 09-10). O 09-04 é de **outro** artefato, `data/ops/refinement_queue.jsonl` (5 linhas). **"Publica" acontece: os 10.337 médios JÁ ESTÃO NO AR, zero esperando.** O que não acontece é **"refina depois"**: **3.101 das 3.201 entradas são páginas VIVAS com defeito nomeado**, e os únicos leitores da fila são o classificador de severidade e dois gates de sitemap — **nenhum consumidor reescreve página**. Dos 55 timers `wikijuridica-*`, **nenhum** é de ingest, reescrita ou refino. Reescritores mortos: `applied_rewrites` desde **27/06**, `shard_rewrite_plan` desde **05/09** |

## 1.13 Fila, erros e custo

- **34.888 `extrair_dispositivos` pendentes**; ~1.200/dia → **~29 dias** em CPU.
- **36 erros** por `done_reason=length` — passaram a escada 512→1024 (`extracao.go:460-476`,
  teto absoluto em `:813`) e morreram no topo, com 3 tentativas. **Veredito medido: (b) ementa
  densa demais para o teto, NÃO laço degenerado.** Quatro evidências:
  1. **Dose-resposta monótona** pelo tamanho da entrada: 0–1k chars **0,00% (0 de 1.632)** ·
     1–2k 0,07% · 2–3k 0,35% · 3–4k 1,22% · 4–5k 1,94% · 5–6k **5,56%**.
  2. **O teto é atingido por trabalho legítimo:** das 5.930 tarefas concluídas com `eval=`, o
     máximo é **1.010 tokens** (teto 1.024) e 163 passaram de 512.
  3. **A assinatura de laço não existe** — laço se apresenta como alto-token/baixo-item. As 8
     que chegaram a 900–1.010 tokens devolveram **16 a 29 dispositivos** (32–58 tok/item);
     nenhuma das 5.930 exibe o padrão.
  4. As 36 são a **cauda**: entrada mediana 3.715 chars (p89) contra 1.640 da população; 30
     menções de dispositivo (p91,6) contra 5; **31 de 36 com ementa estruturada CNJ** contra
     26,5% da população.

  ⇒ **A correção é partir a entrada por item numerado, não "terminal na primeira falha"** —
  que era o que eu havia proposto. **Ressalva medida: 7 das 36 não têm item numerado nenhum** e
  exigem corte por parágrafo. Custo já queimado: **4,74 h de parede**; projeção sobre os 34.796
  pendentes: **~63 falhas ≈ 8 h**.

  *(Esta é a segunda conclusão minha revertida pela medição: eu havia partido da hipótese de
  laço degenerado a partir de uma leitura de `eval` sobre 253 linhas — regex estreita demais.
  A população real são 5.930.)*
- **3 erros** por `ollama: POST /api/generate: HTTP 500: unexpected EOF` — infra tratada como
  conteúdo (`worker.go:121-126`), queimando as 3 tentativas. Medidos: tarefas `956683`,
  `957550`, `957684`, em 14/09 às 16:22, 20:27 e 23:04 — **espalhados por ~7 h, não um evento
  único**. Sem irmã na fila e sem pendente.
- **5 `embed_pagina` em erro são lápides — 5 de 5 confirmadas.** Cada uma tem irmã `concluida`
  com o hash novo, e a irmã concluiu **antes** (02:37–04:40) de o erro ser gravado (08:24).
  **Zero trabalho perdido.**
- **Nas 39 falhas, o conteúdo não se perdeu:** todas já constam em
  `extracoes_dispositivos.jsonl` por `modelo: "parser"`, com 2 a 18 dispositivos cada.
  Perdeu-se a margem do modelo sobre o parser — **que não foi medida** — e a CPU.
- **Correção de caminho:** a fila é **`data/ai/fila.sqlite`** (133 MB, WAL vivo).
  `var/cerebro/` **não existe** — eu havia escrito esse caminho.
- **3 `medir_modelo` paradas** — não por defeito, por **prioridade −10**, abaixo de 8.961
  tarefas de extração.
- Ollama a **~86% de ocupação**; 501 h de CPU em 5,4 dias. O dono declarou que **CPU
  saturada não é o problema**.

## 1.14 Comentários que mentem sobre o próprio dado

`internal/semantica/semantica.go:12-14` diz "10.141 páginas / 41,5 MB" (real: 11.248 /
46 MB). `ops/systemd/wikijuridica-grafo-juridico.service` diz "9,7 s, 13.575 nós, 148.571
arestas" (real: 43,1 s, 79.706, 393.081). O cabeçalho de `tools/generate-grafo-juridico`
afirma que a aresta `aplica` não é populada — há **22.789** hoje. `coleta.go:29` diz que o
maior arquivo mensal tem 360.619 bytes — medi **14.442.367** na Quinta Turma. Pela R1 do
contrato, comentário que mente é bug a corrigir.

## 1.15 ORDEM: toda área do Direito entra na plataforma

**Correção de um erro meu nesta sessão.** Ao analisar as 100 propostas de reescrita, tratei
o fato de virem de acórdãos de Primeira Turma (direito público) como motivo para
considerá-las superadas, porque o acervo publicado é de família, consumidor e trabalho.
**Errado.**

Ordem do dono, literal: *"A plataforma é wiki jurídica, tudo de direito entra na plataforma.
VOCÊ NÃO PODE DESCARTAR."*

**Não existe área do Direito fora do escopo.** Proposta apontando para matéria que o portal
não cobre é **indicação de página a criar**, não material a descartar.

**Correção de outra afirmação minha:** eu disse que o portal "não tem nenhuma dessas áreas".
**Falso.** O acervo cobre 32 áreas, entre elas `previdenciario` 638, `tributario` 473 e
`criminal` 303 páginas. O que é verdade é a **desproporção** — e a causa é a coleta
quebrada, não escolha editorial.

## 1.16 A demanda real do Brasil está no disco e ninguém usa

`data/research/datajud/` tem **22 arquivos com agregado por assunto e tribunal**: **1.022
assuntos, 345.682.422 processos**.

| processos | assunto |
|---|---|
| 20.163.683 | Dívida Ativa (Execução Fiscal) |
| 12.895.909 | Indenização por Dano Moral |
| 12.683.236 | IPTU |
| 8.595.380 | Indenização por Dano Material |
| 6.980.218 | Inclusão Indevida em Cadastro de Inadimplentes |
| 6.588.493 | Auxílio por Incapacidade Temporária |
| 3.224.914 | Tráfico de Drogas e Condutas Afins |
| 3.218.334 | DIREITO PENAL |

As três maiores demandas do país são **execução fiscal, dano moral e IPTU**; o
previdenciário soma quase **14 milhões**; penal e ameaça passam de **9 milhões**. São
exatamente as áreas cujo acervo de jurisprudência não existe porque a coleta aborta antes de
chegar nos datasets correspondentes.

## 1.17 O GATE BURRO: 42% do conteúdo morre numa régua que não é a do gate

**Ordem do dono, 2026-09-15, literal:** *"Tem conteúdo bom, acórdãos etc que podem ir para o
ar, e os gates anulam por burrice."* · *"Os gates têm muitos bugs e travam a fábrica à toa,
sem motivo. Tem molde em decisões em conteúdo, isso é normal."* · *"Ou deixar o gate mais
inteligente ou desativar. Nada trava."* · *"Isso é burrice se você sabe ler e o cérebro
também."*

**Ele está tecnicamente certo, e a medição é esta.** Dos 1.260 candidatos que o gerador
tentou montar numa passada `-seco -limite 500`:

| motivo de recusa | itens | classe |
|---|---|---|
| **`molde_acima_do_limiar`** | **532 (42,2%)** | **JUÍZO** |
| `citacao_abaixo_do_minimo_oficial` | 123 | JUÍZO (orçamento) |
| `ementa_sem_item_transcritivel` | 84 | JUÍZO (regex) |
| `camada_autoral_nao_deixa_espaco` | 21 | JUÍZO (orçamento) |

### Defeito 1 — o produtor não usa a régua do gate que decide publicação

**São CINCO eixos divergentes, não dois** — eu havia achado dois; a medição achou mais três,
e os dois que eu não vi são os que mais pesam:

| # | eixo | gerador (`cmd/generate-acordao-pages`) | gate real (`internal/v2bodyneardup`) |
|---|---|---|---|
| 1 | janela | **3-gramas** (`main.go:103`) | **5-gramas** (`neardup.go:62`) |
| 2 | dígitos | **neutralizados → `"N"`** (`main.go:2187-2196`) | **preservados** (BUG-137 corrigiu justamente para não partir número) |
| 3 | **stopwords** | **mantidas** (`strings.Fields` cru) | **removidas** (`legalsignature.Tokenize`) |
| 4 | **headings** | **incluídos** (`corpoDaPagina`) | **excluídos de propósito** (`AssembleBody:152-154`) |
| 5 | limiar | 0,70 | 0,70 base e **0,82** no gate vivo (`quality.go:84`) |

### A prova: a régua do gerador é ESTRITAMENTE DOMINADA

Medido sobre a população que o gerador de fato carrega para comparar — as **1.134 páginas
publicadas** de `/jurisprudencia/` (1.074 `stj-tema-derivado-01` + 60
`stf-informativo-derivado-01`), **642.411 pares**. Parse validado contra o contador do próprio
gerador (1.134 = 1.134; paridade de `word_count` com mediana |dif| = 0):

| régua | p50 | p90 | p99 | **máx** | pares ≥ 0,70 |
|---|---|---|---|---|---|
| **gerador** | 0,3802 | 0,5205 | 0,6145 | **0,7701** | **135** |
| **gate real** | 0,1291 | 0,2020 | 0,2640 | **0,5193** | **0** |

**Dos 135 pares que o gerador recusa, a régua real aprova 135 de 135** — a 0,70 e também a
0,82. **O inverso é 0.** Não há um único par que o gate real reprove e o gerador aceite.

**O limiar nunca mordeu.** Sob a régua real, o **máximo da família inteira é 0,5193** — muito
abaixo de 0,70 e de 0,82. O 0,70 é a constante herdada do contrato `CONTENT_QUALITY`; a régua
mudou por baixo dela e ninguém recalibrou.

### Cada defeito, isolado (base: os 135 pares recusados)

| variante | p50 | máx | pares ≥ 0,70 |
|---|---|---|---|
| como está hoje | 0,3802 | 0,7701 | **135** |
| **sem neutralizar dígito** | 0,3188 | 0,6879 | **0** |
| **com remoção de stopword** | 0,3149 | 0,7273 | **1** |
| **5-gramas** | 0,3279 | 0,7414 | 6 |
| **sem headings** | 0,3313 | 0,7377 | 14 |

**Qualquer um dos quatro, sozinho, elimina de 121 a 135 das 135 recusas. A neutralização de
dígito zera.**

### A decomposição por camada: o score é a mobília do template

| camada | p50 | p90 | máx | pares ≥ 0,70 |
|---|---|---|---|---|
| **só headings** | **1,0000** | 1,0000 | 1,0000 | **557.002** |
| só FAQ | **0,6867** | 0,8193 | 1,0000 | 292.228 |
| só abertura | 0,4412 | 0,7778 | 1,0000 | 92.126 |
| **só a camada autoral** (`sections.text`) | **0,2469** | 0,3983 | 0,7162 | **1 de 642.411** |

**Os headings são idênticos entre todas as páginas — p50 exatamente 1,0000.** A camada onde
unicidade de fato importa tem **um único par** acima de 0,70 em 642 mil. O detector mede a
mobília que o próprio gerador monta, e é cego para a prosa.

Para o template de acórdão a direção é **mais forte ainda**: os 6 headings embutem
`sigla + numero` (`main.go:1597-1628`), e com dígito → `"N"` viram string idêntica em toda
página. Na amostra mediana: 11,5% dos tokens contêm dígito, **28 números distintos colapsam
num único `"N"`**, e 20,6% da assinatura é afetada.

**As duas divergências somam para o lado severo, e o próprio `CLAUDE.md` §8 já mediu a
primeira:** o mesmo par de páginas dá **0,696 no 5-grama e 0,775 no 3-grama**. Com o mesmo
limiar de 0,70, isso **passa na régua real e morre na do gerador**.

O comentário em `main.go:99-101` **admite a divergência e a justifica**: *"esta régua é a mais
severa das duas, e é a severa que tem de rodar no produtor"*. Severidade sem calibração matou
532 de 1.260. **Nenhuma das 532 foi jamais testada contra a régua que efetivamente decide
publicação.**

### Defeito 2 — neutralizar dígito apaga exatamente o que distingue um acórdão de outro

`shinglesNeutralizados` (`main.go:2187-2196`) faz `reDigito.ReplaceAllString(limpo, "N")`.
Em página de acórdão, **o dígito é o conteúdo**: "REsp 1.794.991" e "REsp 2.150.333" viram o
mesmo shingle; número de artigo, de lei, de súmula e data colapsam junto. A neutralização
nasceu para resolver o problema **inverso** — o §8 do contrato registra "prosa idêntica com
número intercalado". Aplicada a um corpus onde o número é o identificador, ela vira falso
positivo em massa.

### Defeito 3 — o detector mede a fonte e o template, não a nossa prosa

Uma página de acórdão tem três camadas de naturezas distintas:

| camada | quem escreve | molde é… |
|---|---|---|
| ementa oficial citada | **o STJ** | **da fonte** — e a citação identificada é obrigatória (DEC-032) |
| camada autoral | **nós** | **o que importa medir** |
| estrutura + FAQ (`main.go:1597-1628`) | **o template do gerador** | **idêntico por construção** |

`corpoDaPagina` soma as três e compara o total. O score fica dominado pelas camadas 1 e 3 —
que são idênticas **por desenho** — e a camada 2, a única onde unicidade importa, fica
invisível. **O detector está medindo o gerador se acusando de ser um gerador.**

E o dono tem razão no ponto jurídico: **"EMENTA. RECURSO ESPECIAL. PROCESSUAL CIVIL. AGRAVO
INTERNO NÃO PROVIDO."** é linguagem forense padronizada, emitida pelo tribunal. Medir isso
como duplicata nossa é erro de categoria.

### Defeito 4 — o gerador escreve texto próprio demais e depois mata a página por falta de espaço

Em `montaPagina` (`:1630-1670`) a camada autoral e o FAQ são montados **primeiro** e consomem
o orçamento de palavras; só então a citação oficial tenta caber no que sobrou. Se não couber:
`camada_autoral_nao_deixa_espaco_para_citacao` (`:1653`) ou `citacao_abaixo_do_minimo_oficial`
(`:1660`). **144 páginas morrem porque o próprio gerador ocupou o espaço da fonte.** A ordem
de montagem é o defeito, não o conteúdo.

### Defeito 5 — a recusa é terminal e não deixa rastro

As 532 + 123 + 84 + 21 somem a cada passada. Não são gravadas, não entram em fila de refino,
não viram severidade `média` (que o §5 manda publicar e refinar depois), não deixam linha
auditável. **Conteúdo pago some em silêncio.** É a contradição direta do "PUBLICAR E
CORRIGIR" do contrato.

### O que isto NÃO autoriza

**Anti-fraude não se flexibiliza** e **coerência de artefato é inegociável** — campo ausente,
encoding quebrado, corpo vazio e SHA que não bate são **fatos**, não se interpretam. A ética
da OAB continua valendo **onde há publicidade**: promessa de resultado, preço, captação, CTA
comercial.

**O que NÃO é limite:** "risco sob a OAB" em página informativa. Não existe norma disciplinar
sobre precisão de citação em conteúdo informativo, e eu usei essa figura para travar a escala.
Atribuição imprecisa é **defeito de qualidade** (§1.4): conserta-se no produtor, mede-se antes
e depois, e a página **publica e refina**. A arquitetura do P4 é construída sobre essa
separação — FATO, PUBLICIDADE e JUÍZO, cada um com o regime que lhe cabe.

## 1.18 SANGRAMENTO ATIVO: 944 páginas com data de estreia falsa no ar, HOJE

**Este é o defeito mais urgente do repositório, e ele corrompe dado servido a cada onda.**
Medido sobre a **população inteira**, não amostra: das 944 páginas sem registro de estreia,
**944 de 944 trazem `datePublished = 2026-09-15`** no JSON-LD servido em `public/`, e **942
de 944 trazem `dateModified` ANTERIOR ao `datePublished`** — a cronologia impossível que
`cmd/publish-v2-direct/main.go:485-492` declara proibida, viva no ar agora. Exemplo:
`/jurisprudencia/stf-adi-4376/` diz publicado em 09-15 e modificado em 09-05.

**Canais atingidos:** `/jurisprudencia/` 875 · `/leis/` 38 · `/sumulas/` 29 · `/noticias/` 2.

**A cadeia causal, em quatro elos, todos medidos:**

1. `tools/generate-first-published-at` é **órfão** — não está em runner, timer ou hook.
2. `data/editorial/first_published_at.json` está **congelado em 2026-08-28 17:26** (18 dias),
   com **10.107 chaves contra 11.106 do manifesto ⇒ 999 ausentes**.
3. `cmd/publish-v2-direct/main.go:3837` faz
   `ApprovedAt: primeiroNaoVazio(page.PublicationDate, opts.publishedAt)` — sem registro, cai
   no `-published-at "$HOJE"`.
4. **A data anda todo dia:** 900 intents tinham `approved_at = 2026-09-10` no commit
   `315ac61b` e hoje têm `2026-09-15`.

**Segundo consumidor atingido:** `internal/httpserver/api_novidades.go:293` resolve por lookup
em mapa — as 999 saem com **`publicado_em` vazio no canal de máquina**, que é exatamente a
superfície que o §12 do contrato define como o produto.

**E há um elo que realimenta o defeito — com a precisão que faltava.** Eu havia escrito que o
manifesto é *"nunca commitado"*. **Impreciso:** ele **foi** commitado, em `315ac61b` (2026-09-10),
e desde então está `M` no `git status` — 6 dias em 2026-09-16 — enquanto as ondas diárias commitam
estoque e portfólio **sem ele**. O gerador de estreia lê o histórico git do manifesto, então a
fonte que consertaria o dado é a que a onda deixa de gravar (defeito N13).

**E são DUAS causas, não uma — consertar só uma não destrava a outra:**

| # | causa | prova |
|---|---|---|
| 1 | `tools/generate-first-published-at` **é órfão** | **zero invocações**. As duas ocorrências do nome em `cmd/publish-v2-direct/main.go:3597` e `internal/httpserver/api_novidades.go:84` são **comentário**, não chamada — conferido no contexto. Nenhum `.service`, nenhum `.timer`, nenhum passo de deploy, nenhum runner |
| 2 | a onda não commita o manifesto | `315ac61b` é o último; `M` há 6 dias |

*(Nota de método: meu primeiro `grep -rln` devolveu os dois arquivos e eu quase os contei como
chamadores. É a mesma armadilha que já me pegou nesta sessão com `internal/publicrelease`, cuja
única ocorrência em `publish-v2-direct` é um comentário na linha 3772. **`grep` casa comentário;
só o contexto diz se é invocação.**)*

**Ressalva honesta:** o dado é **recuperável** — o gerador reconstrói a estreia a partir do
git. O dano não é perda irreversível: é o artefato **servido** estar errado, e re-datado,
todos os dias, para o Googlebot e para os agentes de IA. Pela matriz do §6, re-datação falsa é
exatamente o que destrói a confiança de crawl.

## 1.19 A onda diária: quatro defeitos novos, e o que esconde a causa dos outros

Além dos sete que eu já havia levantado, a auditoria achou mais, e três formam uma cadeia:

**N2 — `diarios-municipais` morto desde 2026-08-29.** 19 falhas em 32 execuções (as outras 4
fontes: **zero**). De 08-29 a 09-12, "0 de 166 inéditas"; em 09-14 e 09-15,
`tls: handshake failure` em `api.queridodiario.ok.org.br`. **É a causa dominante dos vermelhos
da onda.**

**N1 — e a corrupção do `shfmt` é o que ESCONDE a causa de N2.** Já registrada em §1.7, agora
com o efeito completo medido: (1) `--somente-noticias` roda **zero** coletas (reproduzido);
(2) `daily_content_collect.jsonl` **partiu a série** — chaves antigas param em 09-10, novas
nascem em 09-11; (3) `check-frescor-canal-diario:65-85` tem os nomes **antigos hardcoded**,
então lê um ledger congelado em 09-10 e **cita `(2026-09-10)` na saída de hoje**.
Jurisprudência e súmulas **não conseguem mais reprovar**.

**N8 — o modo `--seco` está MORTO desde 2026-09-09.** `:36` liga `SECO=1`, mas o laço de
`:99-108` (commit `134f4184`) não conhece `--seco`, cai no `*)` e faz `exit 2` em **`:105`,
antes do trap** — sem nem linha de evidência. Reproduzido isoladamente, e consistente com
**0 de 44** linhas com `escopo: "ensaio"` no ledger. **Não existe ensaio da onda há 6 dias.**

**Os demais, todos medidos:** N3 `registra_aviso:47-51` diz no comentário que "anota no
ledger" e só faz `printf >&2`, cujo único chamador (`:546`) manda stderr para `/dev/null` —
**no-op total**. N4 `git add` **por diretório** em `:615` e `:632`, contra o contrato, sem
ninguém olhando às 04:20. N5 `:56` engole falha de escrita do ledger com `2>/dev/null || true`.
N7 `:845` `if [[ -x ]]` sem `else` — gate que perca o bit de execução some em silêncio. N10 a
unit afirma em `:7` que compila no `ExecStartPre`, e **não existe `ExecStartPre=`**. N11 censo
que falha não para a onda, e `internal/v2publish/v2publish.go:239` **não confere frescor** ⇒
publica com a severidade da véspera. N12 `check-onda-avanca:120` só confere que o baseline
**existe**, não que é do dia ⇒ compara contra baseline velho.

**Limpos, e vale registrar:** `:812` (brotli) e `:893` (IndexNow) usam `PIPESTATUS[0]`
corretamente.

## 1.20 O que o crítico de completude achou que ninguém tinha olhado

O workflow de arquitetura terminou 12 dos 13 agentes (a síntese final morreu no limite de
sessão e foi relançada com cache). O crítico de completude trouxe quatro achados novos e
**descartou duas hipóteses medindo-as** — inclusive uma dele mesmo.

### 1.20a A banda de 700 palavras é uma ESCOLHA copiada, não um fato

`cmd/generate-acordao-pages/main.go:74` fixa `pageType = "verbete"`, e `:84-85` copia daí a
banda de **350–700** palavras. Mas `internal/v2ingest/validate.go:54-59` define **quatro**
bandas, e uma delas é **`guia_problema {Min: 700, Max: 1400}`** — o dobro do teto.

É o teto de 700 que produz `orcamento := tetoPalavras - base` (`:1636`) e, dele, **três**
recusas: `camada_autoral_nao_deixa_espaco_para_citacao` (`:1653`),
`citacao_abaixo_do_minimo_oficial` (`:1660`) e `texto_oficial_nao_cabe_na_banda`
(`:1668`/`:1672`). **Medido: 144 de 760 recusas na passada de 500 (18,9%).**

**Segundo aperto no mesmo eixo, e este é autoimposto contra o próprio gate:**
`tetoCitado = 0.42` (`main.go:89`) contra `TETO_CITADO = 0.55` do gate
(`tools/check-derived-authorial-floor:262`) — **24% menos espaço para a camada citada do que o
gate admite**, numa camada que a DEC-032 **obriga**. É a mesma classe de defeito do §1.17: o
produtor mais severo que o gate, sem medição que justifique.

**Nenhuma das três arquiteturas tratou 700 como escolha** — todas o tomaram como natureza.

### 1.20b O piso anti-duplicata de 12 palavras está MORTO no caminho que publica

`duplicatePhraseNgramSize = 12` (`validate.go:24`, `:674-679`) é o detector de frase idêntica.
**Medido: `cmd/publish-v2-direct/*.go` tem ZERO referências a `internal/v2ingest`.** Logo ele
**não roda na publicação**.

E o que ele pegaria, se rodasse, sobre as 1.134 páginas vivas de `/jurisprudencia/`:
**1.134 de 1.134 (100%) compartilham ao menos uma frase idêntica de 12 palavras com outra
página viva**; mediana de **88** doze-gramas compartilhados por par, máximo **422**.

**Ressalva do próprio medidor, e ela é honesta:** `validate.go:21-22` diz *"do mesmo **lote**"*
e ele comparou **todo o canal**; e não aplicou a isenção `maxLegalCitationSpanWords = 40`
(`:41`). Mediana 88 não se explica só por citação legal, mas **o número de reprovações reais
não foi produzido**. Fica como lacuna nomeada, não como conclusão.

**Por que importa:** duas das três arquiteturas propostas apoiavam-se nesse piso como *"o FATO
que sobrevive aos afrouxamentos"*. Ele não está no caminho de publicação.

### 1.20c Terceira divergência produtor↔gate — medida e DESCARTADA

`main.go:770-802` filtra as páginas de comparação por `pagina.PracticeArea != practiceArea`,
**não por família**: a página de acórdão é comparada contra `stj-tema-derivado` e
`stf-informativo-derivado`. O gate canônico faz o oposto — `check-derived-authorial-floor:277-286`
diz literalmente *"Cada família compara SÓ contra si mesma"*.

**É divergência real, e é inócua:** 64.440 pares cross-família, mediana **0,0079**, **máximo
0,0313**, **zero ≥ 0,70**. Registrado aqui justamente para que nenhuma sessão futura gaste
tempo com ela. *(É o padrão que o contrato pede: medir antes de consertar, e escrever o
descarte.)*

### 1.20d `sem_duas_fontes_oficiais_verificaveis` é ramo morto

Não aparece em `recusas` nas passadas `-seco` de 30, 120 nem 500. Uma das arquiteturas
construiu um argumento inteiro sobre ele, e a refutação dela construiu outro. **Zero
disparos** — soma-se aos outros cinco cortes que nunca mordem (§1.17).

### 1.20e Os 49.807 agravos: 2.902 passam TODO o resto de `elegivel`, e a rota já existe

| medição sobre a população inteira | N |
|---|---|
| procedimentais por `procedimental()` (`main.go:316-324`) | 49.807 de 60.221 (82,7%) |
| **passam todo o resto de `elegivel`** (ACÓRDÃO + campos + ementa ≥ 250 + âncora substantiva) | **2.902** |
| anunciam mérito alcançado no REsp (regex, não veredito lido) | 4.792 |
| nos dois conjuntos | 270 |
| `AREsp` puro | 11.553 (505 dentro dos 2.902) |

**Lidos 5 dos 2.902 por stride (amostra de 5, não população): 3 de 5 são mérito real**, com
número: `AgInt no AREsp 2119967` (art. 18 §1º do CDC, prazo de 30 dias para sanar vício),
`AgInt nos EDcl no REsp 2109469` (art. 205 do CC, retenção de 25% em rescisão), e
`AREsp 2352762` — *"AGRAVO CONHECIDO PARA NEGAR PROVIMENTO AO RECURSO ESPECIAL"*, art. 628 §2º
do CPC. Os outros 2 são admissibilidade.

**A rota de agregação JÁ EXISTE no repositório e já consome procedimentais:**
`cmd/generate-lei-artigo-pages:485-500` indexa **todo** registro por URN e acumula `Orgaos`,
`Classes`, `Relatore`, `Sumulas`; `:1481` publica *"A classe processual mais frequente é …"*.
**Os agravos entram lá como CONTADOR, nunca como texto.** E esse gerador é um dos órfãos: não
está em `tools/run-daily-content:368-373`, que lista cinco.

⇒ **Não é preciso construir rota nova para os procedimentais: é preciso ligar a que existe** e
promover o agravo de contador a fonte de conteúdo agregado. Mais: **separar `AREsp` de
`AgInt`** — o `AREsp` é o veículo em que o STJ decide o mérito do próprio recurso especial, e o
filtro por `strings.Contains` o varre junto com o agravo interno.

### 1.20f CONFLITO ENTRE DOIS AGENTES, registrado sem escolha silenciosa

Dois agentes independentes mediram *"dos ~4.500 barrados por ementa curta, quantos têm âncora
substantiva"* e **não convergiram**:

| agente | resultado |
|---|---|
| agente de pisos | **2.477** com âncora substantiva |
| crítico de completude | **1.225** substantiva · 1.238 qualquer URN · 1.518 qualquer URN ou súmula |

O crítico **testou três definições e nenhuma chega a 2.477**, e propôs como estrato
honestamente recuperável **805** (ementa ≥ 150 palavras **e** âncora substantiva). Também
divergem no total barrado: 4.500 (Go) contra 4.498 (réplica do crítico, que declara a
aproximação — `[0-9A-Za-zÀ-ÿ]+` contra `ptbrtext.BodyWords`).

**Hipótese de desempate, e ela é medível em uma passada:** o agente de pisos provavelmente
contou **com** a sobreposição do cérebro (`data/ai/dispositivos_promovidos.jsonl`) e o crítico
**sem** — a sobreposição é exatamente o que move `sem_ancora_legal_substantiva` (de 3.354 para
1.151, §1.3). **A diferença 2.477 − 1.225 = 1.252 é da ordem das 2.203 promoções**, o que
sustenta a hipótese.

**Como se fecha, e entra no §4.2:** rodar a contagem com e sem `CarregaSobreposicao`, sobre
snapshot datado do overlay (que muda durante a medição, §1.3), com o tokenizador do Go. **Até
lá, o plano usa a faixa `805 ≤ x ≤ 2.477` e nomeia a incerteza** — nenhum dos dois números
entra como fato.

### 1.20g Uma proposta do crítico, testada e descartada por ele mesmo

**4.447 dos 4.498** acórdãos de ementa curta têm campo `dispositivo` com ≥ 25 palavras — o que
sugeriria tirar dali a camada citada e resolver o problema do piso. **Ele leu 3 de 3 amostrados
e descartou:** é a **fórmula de votação** — *"Vistos, relatados e discutidos estes autos,
acordam os Ministros da TERCEIRA TURMA … por unanimidade, dar provimento ao recurso especial,
nos termos do voto do Sr. Ministro Relator…"*. **Não é camada citada de substância.**

Registrado porque é o tipo de rota que parece obviamente boa por contagem e morre na leitura —
e porque medir custa menos que implementar.

## 1.21 BASELINE AO VIVO — medido em 2026-09-15 ~18h, é o "ANTES" de todo runbook

Ordem do dono: *"sempre fazer testes reais, testar no servidor, testar ao vivo a produção, ver
comportamento dos bots de IA que estão entrando sempre"*. Medido agora, com a identidade
`wikijuridicabot` e `X-Warming-Request: true` para não entrar na métrica:

### Produção — no ar e saudável

| camada | resultado |
|---|---|
| borda (`https://wikijuridica.com.br/`) | **HTTP/2 200**, 0,158 s |
| nginx origem (`127.0.0.1:8088`) | **200**, **0,54 ms** |
| Go (`127.0.0.1:8089/familia/index.md`) | **200**, 3,2 ms |

**E a borda confirma o defeito do P1b por via independente.** Em
`/jurisprudencia/stf-adi-4376/` — a página que o agente citou como exemplo de cronologia
impossível:

```
cache-control: public, max-age=86400, s-maxage=604800
last-modified: Sat, 05 Sep 2026 00:00:00 GMT
age: 27291        (7,6 h de cache)
cf-cache-status: HIT
```

**O `Last-Modified` do HTTP diz 05 de setembro. O `datePublished` do JSON-LD diz 15 de
setembro.** A página afirma ter sido publicada dez dias **depois** da última vez que mudou.
Dois instrumentos independentes — o header servido pela Cloudflare e o JSON-LD no HTML —
discordam, e o que está errado é o JSON-LD. Confirmação externa do §1.18.

### Cérebro — trabalhando agora

| medida | valor |
|---|---|
| `wikijuridica-cerebro` / `ollama` | **active / active** |
| residente | `qwen3.5:4b`, `size` **3,01 GiB**, **`size_vram` = 0,0** |
| fila `data/ai/fila.sqlite`, tabela `tarefa` | **53.786 linhas** |
| `extrair_dispositivos` pendente | **34.217** |
| `extrair_dispositivos` **executando** | **3** — está processando neste instante |
| `extrair_dispositivos` concluída | 8.271 · erro **39** |
| `embed_pagina` concluída | 11.248 · erro 5 |
| `medir_modelo` pendente | 3 |

**`size_vram` aparece no `/api/ps` valendo 0,0** — confirma ao vivo as duas coisas que o agente
de GPU mediu: o campo **existe** (e `internal/ollama/cliente.go:275-280` o descarta em
silêncio), e **o predicado de spill que eu havia proposto (`size_vram < size`) pausaria o
cérebro agora, para sempre**, porque em CPU puro ele é verdadeiro em todo residente.

### Bots — medidos NA BORDA, que é a única fonte com autoridade

**Correção de um erro meu, e ele é de método, não de digitação.** Eu havia escrito "943
requisições em 6 h" lendo `data/ops/ai_citation_signal_daily.jsonl`, que mede a **ORIGEM**. O
próprio arquivo declara, e eu transcrevi a frase sem agir sobre ela: *"origem ≤ borda SEMPRE:
HIT na borda não toca a origem"*. A página que sondei voltou `cf-cache-status: HIT` com
`s-maxage=604800`. **Quase todo bot nunca chega à origem.** O dono corrigiu: *"você não pode se
basear em números mentirosos… a plataforma tá funcionando e você tá limitando meu trabalho a
números mentirosos"*.

**Medido na API da Cloudflare** (`tools/cloudflare_auth.py`, escopo `leitura`,
`httpRequestsAdaptiveGroups`, janela `2026-09-15T00:16Z → 2026-09-16T00:16Z`, 24 h):

| medida | valor |
|---|---|
| **requisições totais na borda** | **88.033** |
| **bots identificados** | **17.325 (19,7%)** |
| user-agents distintos (topo da consulta) | 200 (limite da consulta, não da realidade) |

| agente de IA | 24 h | crawler de SEO/outros | 24 h |
|---|---|---|---|
| **amazonbot** | **3.446** | ahrefs | 5.919 |
| **oai-searchbot** | **1.234** | semrush | 2.447 |
| **chatgpt** | **1.099** | petalbot | 1.018 |
| applebot | 519 | bingbot | 516 |
| **perplexity** | **361** | facebookexternalhit | 324 |
| **gptbot** | **241** | googlebot | 111 |
| meta-externalagent | 18 | dotbot | 37 |
| claude-user | 3 | yandex | 32 |
| **subtotal IA** | **6.921** | | |

**A ordem de grandeza do meu erro: ~3.800 (origem, extrapolado) contra 17.325 (borda) — 4,6× no
recorte de bot, e o total de 88.033 requisições que a origem nunca vê.** O `edge_reconciliation`
do próprio arquivo nomeia a causa: *"o quociente entre as duas séries é fan-out de cache, não
erro de medição"* — o erro foi **meu**, ao usar a série de origem como se fosse de volume.

**Consequência para todo este plano:** onde ele fala de tráfego, alcance ou retorno de bot, a
autoridade é a **borda**. A série de origem serve para **piso** e para o que só existe na
origem (rota dinâmica, gêmea Markdown, `/api/v1`, MCP — que não são cacheadas do mesmo modo).
Isto virou regra 15 do `CLAUDE.md` (§P0).

**E não há "janela de horas" a esperar:** o tráfego de agente é contínuo e a API da borda
responde a consulta de 24 h em uma chamada. O que o runbook mede depois de publicar é a **rota
nova** aparecendo na borda — não a existência de tráfego, que é permanente e alta.

**E a série já declara honestamente o que NÃO mede** (campo `nao_mensuravel`), o que é o padrão
que o plano deve seguir: citação sem clique (com zero-clique na casa dos ~68%, provavelmente o
maior componente, e não deixa rastro na origem), resposta pela memória do modelo, *fetch*
descartado, clique com `Referer` suprimido, e conversão. Também declara a reconciliação
borda↔origem: *"origem ≤ borda SEMPRE: HIT na borda não toca a origem. O quociente entre as
duas séries é fan-out de cache, não erro de medição."*

**Regras de exclusão de tráfego próprio já implementadas** (é o que impede o portal de medir o
próprio eco): cabeçalho de simulação marcado pelo nginx, campo `warm` no log, UA com prefixo
`wikijuridica-`, IP não público, e `Referer` interno.

---

# 2. O plano

> ### MAPA DE LEITURA — a ordem de EXECUÇÃO não é a ordem do documento
>
> As seções cresceram por ordem de descoberta, não de execução. **A ordem que vale é a do
> roteiro**, e é esta — quem executar segue a coluna da esquerda, não a posição no arquivo:
>
> | ordem de execução | seção | posição no documento |
> |---|---|---|
> | 1 | **P−1** gravar o plano no repo e commitar | logo abaixo |
> | 2 | **P0a** modo operacional do Claude Code (crítico) | logo abaixo |
> | 3 | **P0c** reescrever os contratos + teste | logo abaixo |
> | 4 | **P0d** gravar o aprendizado no repo | logo abaixo |
> | 5 | **P0b** modernizar a memória | logo abaixo |
> | 6 | **P0** as 21 regras do `CLAUDE.md` (fonte; o P0a manda no formato) | **no fim do §2** |
> | 7 | **P1b** estancar as 944 datas falsas no ar | logo abaixo |
> | 8 | **P1** destravar a coleta do STJ | logo abaixo |
> | 9 | **P2** desfazer a corrupção do shfmt | logo abaixo |
> | 10 | **P3** matar os produtores órfãos | logo abaixo |
> | 11 | **P6 (a)** travessia mínima, com `lane`/`pageType` corrigidos | logo abaixo |
> | 12 | **P4** paridade de régua, piso na saída, regex em fallback | **depois do P9** |
> | 13 | **P6 (b)** `-seco` de recenseio e o lote | idem 11 |
> | 14 | **P7** destravar o DataJud | logo abaixo |
> | 15 | **P5** fechar a lacuna de atribuição (paralela, não bloqueia) | logo abaixo |
> | 16 | **P8** nenhum conteúdo parado | logo abaixo |
> | 17 | **P9** independência e auto-recuperação | logo abaixo |
> | 18 | **P10** produto do cérebro sob CI | logo abaixo |
> | 19 | **P13** medir citação de IA como rotina, e crescer IA-first | logo abaixo |
> | 20 | **P11** canal social (critério de destrava escrito, não destrava ainda) | logo abaixo |
> | 21 | **P12** documento da IA local para a GPU | logo abaixo |
> | — | **P14** rede social de IA — **rascunho, só documenta após a aprovação** | logo abaixo |
>
> **Duas amarras que atravessam tudo e não têm seção própria:** o `stop` de
> `wikijuridica-server-reload.path` é **pré-condição de toda transação** (§2.9.1 A1), e o
> **passo 2.6 do `deploy-publico`** (índice de co-citação) é obrigatório em **todo** bloco que
> republica — P1b inclusive (§2.9.6).

## P−1 — Gravar este plano no repositório e commitar: a AÇÃO Nº 1

**Ordem do dono, 2026-09-15:** *"Coloque no plano que a primeira coisa que vai fazer é criar um
arquivo desse plano e commit."*

**E o motivo já se materializou nesta sessão:** o processo caiu, o limite de sessão matou dois
agentes no meio do trabalho, e este plano — **152 KB de medição paga, com dezenas de
`arquivo:linha` conferidos e quatro conclusões minhas refutadas por agentes** — vive em
`~/.claude/plans/`, fora do git. Não é versionado, não sobrevive a `/clear`, e nenhuma sessão
futura o encontra.

**Execução, nesta ordem, antes de qualquer outra frente:**

1. `docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` — este documento, íntegro, com a data no nome
   (o contrato §12 manda que parágrafo superado ganhe data e motivo, e nunca seja apagado).
2. Os registros duráveis que os agentes produziram vão junto, como anexos de medição — são a
   evidência primária de cada número deste plano:
   `pure-imagining-cerf-agent-a0fc779a1c55a9565.md` (systemd, namespace, ledger de falhas),
   `-af465413c160d39d0.md` (GPU: `size_vram`, sm_120, `ollama#18232`),
   `-a38835ca3a6cba692.md` (réguas de molde, curva de rendimento, 36 truncadas),
   `-aab45dc3ef36a59ab.md` (onda diária, `first_published_at`, 20 units mascaradas),
   `-aabb63b7c2590de9e.md` (pisos, regex de itens, catálogo de admissibilidade).
3. **Commit leve** — é dado e documento, não Go: não precisa do `flock` pesado
   (`/tmp/opt-wiki-agent-heavy.lock`), e pelo §1 do contrato commit de conteúdo deve ser
   frequente e concorrente, com retry curto no `index.lock`.
4. `git add <caminho exato>` de cada arquivo, **nunca por diretório** (já varreu trabalho de
   outra sessão três vezes), e `git commit -F <arquivo>` em comandos **separados** — juntos, o
   pre-commit reprova com *"índice mudou durante compilação"*.
5. **Registrar em `docs/goal/MAESTRO_CODEX_LOG.md`** o que este plano decide e por quê — é o
   canal que o §11 do contrato nomeia para mudança de política.

**Prova de aceitação:** `git log --oneline -1 -- docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md`
devolve o commit; `git show HEAD:docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md | wc -l` bate com
o arquivo local; e nenhum dos cinco anexos fica `untracked` (o §"Produto não fica untracked" do
contrato de máquina).

## P0a — CRÍTICO: mudar o MODO OPERACIONAL do Claude Code neste repositório

**Ordem do dono, 2026-09-15:** *"Revise as regras e deixa elas mais operacionais e modo
engenharia padrão Anthropic… com engenharia de qualidade e com obediência às regras, evitando
retrabalho, gasto de tokens errado e melhorando eficiência… Vamos mudar o modo operacional do
Claude Code neste repo, com caminhos corretos, engenharia correta e nada solto e nada
hardcoded."* **Classificada por ele como CRÍTICA.**

### REFUTAÇÃO da minha hipótese: o defeito não é visibilidade, é densidade

Eu havia diagnosticado *"regra amarrada a tema em vez de ato, ninguém lê no momento certo"* e
proposto mover para documento com gatilho. **A auditoria mapeou cada erro contra onde a regra
vivia, e me derrubou:**

| erro que cometi | onde a regra estava | estava em contexto? |
|---|---|---|
| reabri o DataJud | `CLAUDE.md:72-92` | **sim** |
| inventei risco da OAB | `CLAUDE.md` §8 | **sim** |
| devolvi decisão ao dono | `~/.claude/CLAUDE.md` | **sim** |

**Três dos cinco erros aconteceram com a regra carregada no contexto.** Isso mata "mover para
doc e criar gatilho" como remédio — o problema não é que ninguém leu. É que **22.358 tokens
fixos por sessão** afogaram a imposição no argumento.

**E no caso do DataJud a prosa é ativamente nociva:** são vinte linhas no formato *"há quem diga
X, mas na verdade Y"*, e elas **reconstroem a dúvida que pretendiam fechar**. Ler o contrato me
deixou menos decidido do que não tê-lo lido. Esse é o mecanismo exato do *"você sempre sabota"*.

⇒ **Daí um quarto destino, além de hook, skill e doc: VEREDITO ADOTADO.** Uma linha imperativa,
com data e caminho do parecer, **sem o porquê**. O raciocínio vai para o documento; o contrato
fica com a decisão.

### O custo fixo real, medido

| fonte | tokens por sessão |
|---|---|
| `CLAUDE.md` do repo | **11.962** |
| `~/.claude/CLAUDE.md` | 3.765 |
| índice de memória | 6.631 |
| **total fixo** | **22.358** |

*(Minha estimativa anterior de ~16.200 estava baixa: eu não contei o índice de memória.)* Mais
**100.512 tokens de memórias linkadas** que entram apenas como título de uma linha — e foi
exatamente ali que morava *"o dono não revisa páginas"*.

**A tabela "Leitura obrigatória, por gatilho" do §2 pede 64.979 tokens de leitura**, sendo
15.211 só antes do primeiro comando. **Nenhuma sessão paga isso. Por isso ela não funciona** —
e a correção não é melhorar o gatilho, é não depender dele.

### Três decisões corrigidas pela documentação oficial

A auditoria propôs, a doc contrariou, e o desenho mudou:

1. **`.claude/rules/*.md` com `paths:` é nativo** — o hook que eu ia construir reimplementava,
   pior, o que o harness já faz. Virou **6 regras por caminho, custo fixo zero**.
2. **`.claude/commands/` é formato legado** — o diretório de skill já é o comando. Os 5 slash
   commands viraram **skills**.
3. **`ask` não garante que a razão chegue ao modelo.** Cinco hooks pediriam confirmação ao dono
   sem ensinar nada — que é o erro nº 3 (devolver decisão) **disfarçado de guarda**. Todos
   passaram a emitir `hookSpecificOutput.additionalContext`.

### O que a medição desmentiu sobre custo

- **Hooks são baratos hoje:** pior hook **16,6 ms**, paralelo 36 ms contra 75 ms serial, e
  `--max-ms 300` passa com exit 0. **A memória dos 13,97 s é histórica** — o caro é
  `SessionStart`, e nenhum hook novo o usa.
- **A economia de tokens é benefício secundário, não primário.** `ai-tokens` mostra **cache-read
  em 97% do volume**: os ~8.200 tokens/sessão economizados se multiplicam pelos turnos (~1,3 M
  numa sessão longa) **e ao mesmo tempo são o token barato**. **O ganho que importa é o
  retrabalho** — os três erros que aconteceram com a regra visível.
- **Só o §10 do `CLAUDE.md` tem teste.** §1–§9, §11 e §12 **não são cobrados por nada**.

### Hardcoded, medido

- **`0,70` em 6 constantes mais 2 usos inline, sem um único import entre elas.** Vai para **uma
  constante Go** — e **não** para JSON: `fiscalization.go:182` registra que é valor **calibrado**
  contra o model2vec, e valor calibrado não é configurável.
- **47 literais de runtime do domínio em arquivos `.go`** — e o teste que deveria impedir isso,
  `site_url_flexibility_test.go`, **não varre o domínio**: só `Rafael Toledo`, `227191` e
  `OAB/RJ`. **A cerca existe, é bem feita, e não cobre justamente o valor que o contrato mais
  afirma estar centralizado.**
- `HTMLBudgetBytes` duplicado em 4 pacotes · `DefaultMainRoot = "/opt/wiki"` ·
  `/home/rafael/go/bin` em 4 units · `cloudflared` com caminho **e versão** no `ExecStart`.

### Doze fatos obsoletos, e um deles é risco operacional

Os 8 que eu tinha, mais 4 novos. Páginas 11.039 → **11.106** · Go 2.493 → **3.259** · pacotes
488 → **585** · severidade 100/9.394/747 → **119/10.337/769** · HTML 22.631 B/10.369 →
**23.414 B/11.358** · grafo 9,7 s/13.575 → **43,1 s/79.706** · aresta `aplica` "não populada" →
**22.789** · embeddings 10.141/41,5 MB → **11.118/49,7 MB**.

**O novo que é urgente:** `coleta.go:29` afirma que o maior arquivo mensal tem 360.619 bytes.
**O real é 26.704.470 — 74× maior.** O `LimiteArquivoMensal = 64 << 20` tinha folga de 178×;
agora tem **2,5×**. *"A folga de 64 MB deixou de existir"* — e o P1 recupera 391 competências,
incluindo as turmas de maior volume. **Isso entra no P1 como verificação antes da recuperação.**

**E a correção estrutural vale mais que consertar as doze linhas:** **nenhum número de estado
vive no contrato.** Número de estado envelhece por construção; o contrato diz **onde medir**,
nunca **quanto é**. Cobrado por asserção de teste.

### O desenho resultante

`CLAUDE.md` de **11.962 → ~3.294 tokens** redigidos (teto de 4.500 em teste) · **11 hooks** ·
**6 regras por caminho** · **8 skills** · testes T1–T5 mais `tools/check-modo-operacional` ·
e **5 ondas de execução em que nenhuma linha de prosa sai antes de o mecanismo substituto estar
no disco, testado, e medido disparando.**

### O diagnóstico original, que a refutação acima corrige em parte

**As regras existiam e as sessões não as seguiram.** Nesta sessão o dono teve de repetir a mesma
correção em cinco formas diferentes:

| o que eu fiz de errado | a regra já existia? |
|---|---|
| reabri o DataJud, que ele manda destravar *"sempre"* | parcialmente — o §2 já dizia que API pública é livre |
| inventei risco da OAB para travar conteúdo informativo | o §8 já limitava a ética a publicidade |
| medi tráfego na camada errada e publiquei o número curto | o próprio arquivo declarava `is_lower_bound` |
| devolvi decisão a ele **três vezes** | o contrato de máquina já proibia |
| desenhei "revisão humana" como etapa de esteira | ele já havia dito que é impossível |

**Nenhum desses erros foi por falta de regra escrita.** Logo o defeito é de **arquitetura de
instrução**: regra escrita em prosa, num documento longo, amarrada a **tema** em vez de **ato**,
sem imposição executável. **Regra que depende de alguém lembrar de ler não é regra: é
esperança.**

### O princípio da reescrita

> **Regra que pode ser IMPOSTA não se escreve: implementa-se.** Cada regra vai para o mecanismo
> que a torna inevitável — hook que bloqueia, gate que reprova, permissão que nega, skill que
> carrega o procedimento no momento da ação. Só fica no `CLAUDE.md` o que é **fato do projeto**,
> porque é o único conteúdo que justifica custo de token em toda sessão.

| natureza da regra | mecanismo certo | exemplo desta sessão |
|---|---|---|
| **proibição** | **hook** que bloqueia com mensagem que ensina o caminho | *"nunca `cmd/check` sem argumento"* é uma frase hoje; devia ser um hook — ele já levou o load a 52 |
| **invariante** | **gate** / teste de contrato | régua do produtor **é** a do gate (§P4) |
| **procedimento longo** | **skill**, carregada por descrição no momento certo | a cadeia de deploy, a ordem topológica dos ~9 derivados |
| **comando repetido** | **slash command** | a verificação ao vivo da produção |
| **saída grande** | **MCP** (`context-mode` já existe) | medição sobre 60.221 registros |
| **fato do projeto** | **`CLAUDE.md`** | topologia, identidade do bot, onde mora o quê |
| **caso e aprendizado** | **`docs/` com gatilho por ATO** | §P0d |

### O que a documentação OFICIAL da Anthropic diz — e três achados urgentes

Colhido do especialista em Claude Code, com URL por recomendação.

**ACHADO 1 — O `MEMORY.md` está a 6,4% do teto de truncamento silencioso.** Medido agora:
**167 linhas, 23.970 bytes (23,4 KB)**. O limite oficial é **os primeiros 200 linhas OU 25 KB,
o que vier primeiro**, e *"content beyond that threshold is not loaded"* — **silenciosamente,
a cada nova sessão**
([memory#auto-memory](https://code.claude.com/docs/en/memory#auto-memory)). Restam **1.054
bytes** e 33 linhas. **As quatro memórias novas do §P0b estouram o teto**, e o que passar do
corte desaparece sem aviso. ⇒ O §P0b ganha um passo: **compactar o índice antes de acrescentar**,
e um gate que reprove `MEMORY.md` acima de 24 KB ou 190 linhas.

**ACHADO 2 — os dois `CLAUDE.md` custam ~16.200 tokens em TODA sessão, e são 3,2× o alvo.**

| arquivo | linhas | bytes | tokens (est.) | alvo oficial |
|---|---|---|---|---|
| `/opt/wiki/CLAUDE.md` | **645** | 43.142 | ~12.300 | **< 200 linhas** |
| `~/.claude/CLAUDE.md` | **270** | 13.584 | ~3.900 | **< 200 linhas** |
| **soma, por sessão** | **915** | 56.726 | **~16.200** | |

*Método: bytes ÷ 3,5 para PT-BR; é estimativa declarada, não contagem de tokenizador.* E a
documentação é explícita sobre a consequência: *"Longer files consume more context and **reduce
adherence**"*
([memory#write-effective-instructions](https://code.claude.com/docs/en/memory#write-effective-instructions)).
**O arquivo longo é causa do problema, não só custo.**

**ACHADO 3 — e este é uma correção contra mim.** A documentação de prompting recomenda o
oposto do que eu vinha fazendo: *"Instead of 'CRITICAL: You MUST use this tool when…', use more
normal prompting like 'Use this tool when…'"* — linguagem densa em maiúsculas e imperativos
**pode overtriggerar** em modelos recentes
([prompting-best-practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#tool-use)).
Este plano está cheio de **PROIBIDO** e **OBRIGATÓRIO** em caixa alta. **A reescrita troca
ênfase tipográfica por especificidade verificável:** não *"medir na borda"* em maiúsculas, e sim
o comando, o arquivo e o número esperado.

### As cinco causas documentadas de as sessões não obedecerem

1. **`CLAUDE.md` chega como MENSAGEM DE USUÁRIO, não como system prompt** — daí *"no guarantee
   of strict compliance… especially for vague or conflicting instructions"*
   ([memory#troubleshoot](https://code.claude.com/docs/en/memory#claude-isnt-following-my-claude-md)).
   Regra que precisa ser garantida **não pode viver ali**.
2. **Subagente NÃO herda a auto memory do pai** (só o `fork` herda)
   ([sub-agents](https://code.claude.com/docs/en/sub-agents)). **Isto explica diretamente por que
   os mesmos erros voltam:** a lição aprendida não chega ao próximo agente. O campo `memory:` no
   frontmatter dá memória própria ao subagente — é a correção.
3. **`@import` NÃO economiza contexto:** *"imported files still load and enter the context window
   at launch"* ([memory#import](https://code.claude.com/docs/en/memory#import-additional-files)).
   Organizar por import não reduz um token.
4. **Não há algoritmo de precedência entre `CLAUDE.md` conflitantes** — a doc diz que o mais
   específico *"typically"* vence, e que *"Claude may pick one arbitrarily"*. ⇒ **a precedência
   tem de ser declarada por escrito**, e conflito entre níveis é defeito a eliminar.
5. **Comentário HTML de bloco é removido antes de entrar no contexto** — não custa token. É onde
   nota de manutenção deve morar.

### Os mecanismos oficiais que o repo ainda não usa

| mecanismo | o que resolve | fonte |
|---|---|---|
| **`.claude/rules/` com `paths:`** | regra que carrega **on-demand**, só para arquivos que casam com o glob | [large-codebases](https://code.claude.com/docs/en/large-codebases#choose-between-per-directory-claude-md-and-path-scoped-rules) |
| **`hookSpecificOutput.additionalContext`** | **injeção condicional de contexto**: o hook roda no evento e devolve a regra certa no momento do ato. É a resposta oficial para *"ninguém lê o documento na hora certa"* | [hooks](https://code.claude.com/docs/en/hooks-guide#json-output-format) |
| **campo `if` no hook** | filtra por permissão — ex.: roda só se o comando casar com `Bash(rm *)` | [hooks](https://code.claude.com/docs/en/hooks-guide) |
| **`InstructionsLoaded` hook** | **audita** quais arquivos de instrução carregaram, quando e por quê | [memory#troubleshoot](https://code.claude.com/docs/en/memory#troubleshoot-memory-issues) |
| **`CLAUDE.md` por subdiretório** | carrega quando o Claude trabalha ali; aditivo, sem override | [large-codebases](https://code.claude.com/docs/en/large-codebases#layer-claude-md-files-by-directory) |
| **`memory:` no frontmatter de subagente** | memória própria do subagente, que hoje não existe | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| **`skills` pré-carregadas no subagente** | garante que o agente nasça com o procedimento certo | [sub-agents](https://code.claude.com/docs/en/sub-agents) |

**Custo de cada mecanismo, oficial:** `CLAUDE.md` = conteúdo inteiro, **toda requisição**;
skill = **só a descrição** no launch (truncada em 1.536 caracteres), conteúdo ao invocar;
MCP = nomes das ferramentas no launch, schemas sob demanda; **hook = ZERO, a menos que devolva
output**; subagente = contexto **isolado**
([context-window](https://code.claude.com/docs/en/context-window)).

**E o que a documentação NÃO cobre — declarado, não preenchido com inferência:** custo em tokens
do `additionalContext` de hook; *prompt caching* aplicado a instruções; precedência computável
entre `CLAUDE.md` conflitantes; e o custo comparativo de um `CLAUDE.md` longo contra o conjunto
equivalente de skill + rules. **O último se mede aqui, e vira o número do item 8 desta frente.**

### As três investigações em curso — nenhuma fica para depois

1. **Especialista em Claude Code da Anthropic** (`claude-code-guide`): a orientação **oficial**,
   com URL, sobre estrutura e tamanho de `CLAUDE.md`, onde cada tipo de regra deve morar, como
   se redige instrução que o modelo de fato segue, eventos de hook e **injeção condicional de
   contexto**, carregamento de skill, eficiência de contexto e `prompt caching`, `settings.json`
   e boa prática de subagente. Com ordem explícita de dizer *"a documentação não cobre isto"*
   em vez de preencher com inferência — porque isto vira contrato executável.
2. **Auditoria do modo operacional atual**: inventário com tamanho e **custo estimado em
   tokens** dos dois `CLAUDE.md` (que entram em **toda** sessão), de `.claude/` (skills, hooks,
   agents, settings, commands), dos hooks de máquina com o custo de cada um, e de quais testes
   de `internal/contract/` travam qual documento. Mais a classificação bloco a bloco:
   **IMPOSIÇÃO · PROCEDIMENTO · SAÍDA GRANDE · FATO · OBSOLETO**.
3. **A caça ao hardcoded**, que o dono nomeou: caminho absoluto que deveria ser derivado, número
   mágico que deveria vir de config ou de medição, e identidade literal onde deveria haver
   função. **Dois já conhecidos:** `limiarMolde = 0.70` e `pisoEmentaPalavras = 250` — este
   calibrado para *"sobrar 1.674 candidatos"*, ou seja, para o **tamanho do pool**, não para
   qualidade. O repositório já tem a disciplina certa em dois pontos e ela precisa valer em
   todos: UA **nunca** escrito à mão (é `wikijuridicabot.Aplica`) e a nota de método é
   `editorial.MethodDisclosure(autor)` — **função, não constante**, porque há teste que reprova
   identidade literal em runtime.

### O que a reescrita tem de entregar

1. **Estrutura nova do `CLAUDE.md`**: o que fica com justificativa de custo fixo, o que sai, e
   para onde vai.
2. **Tabela de migração**: bloco atual → mecanismo novo → arquivo a criar.
3. **Hooks a criar**: evento, o que bloqueia, **a mensagem que ensina o caminho certo** (hook que
   só nega ensina nada), e custo alvo — o custo de um evento é o do hook **mais lento**, não a
   soma, e já houve `true` custando 13,97 s.
4. **Skills a criar**: nome, descrição de acionamento, conteúdo.
5. **Des-hardcodificação**: cada valor fixo, onde passa a morar, como se deriva.
6. **Correção dos fatos obsoletos** (oito já medidos, §regra 19), com o número real.
7. **Teste de contrato** que cobra o que não pode sumir (§P0c).
8. **Economia estimada de tokens por sessão**, com método declarado.

**Por que isto é crítico e vem cedo:** todas as 14 frentes seguintes são executadas **por
sessões de Claude Code**. Se o modo operacional não muda, a execução repete os erros desta
sessão — e o dono paga duas vezes pelo mesmo trabalho.

## P0c — REESCREVER os contratos sob a política nova (mandato expresso do dono)

> ### MANDATO DE REESCRITA
>
> **Ordem do dono, 2026-09-15, literal:** *"Você tem o dever de reescrever os contratos com nova
> política. Eu tô mandando, coloque no plano."*
>
> **Isto não é emenda: é reescrita.** Até aqui o plano falava em *acrescentar regras*. A ordem
> é mais ampla e mais alta: **os contratos passam a ser redigidos sob a política nova**, e o
> Claude Code tem o **dever** de fazê-lo — não a permissão de sugerir.
>
> **O que a reescrita corrige, e é o que o dono vem apontando a sessão inteira:**
>
> | defeito do contrato atual | o que a reescrita faz |
> |---|---|
> | regra escrita com **adjetivo** ("medir na borda", "ser conservador") | regra com **comando, caminho e número esperado** |
> | regra ligada a **tema** ("sobre medição") | regra ligada ao **ato** ("antes de afirmar volume") |
> | prudência genérica que vira freio | **teto só com causa física externa medida** |
> | contrato que descreve o que **é** | contrato que diz o que **se faz**, na ordem |
> | regra em um documento só | **bloco canônico replicado e cobrado por teste** |
>
> **O que a reescrita NÃO faz, e é limite do próprio contrato:** não apaga parágrafo — parágrafo
> superado **ganha data e motivo** (§12) —, não afrouxa anti-fraude, coerência de artefato,
> ética de publicidade nem citação legal, e não remove regra que custou incidente. **Reescrever
> é tornar operacional o que já vale, e acrescentar o que faltava.**
>
> **Autorização registrada:** o §11 do contrato já dizia que se **pode e deve** ampliar
> documentação, contratos e políticas quando isso destrava o projeto, editando para frente. A
> ordem de hoje transforma isso em **dever**, com data.

> ### E NÃO CONFIAR NO CONTRATO COMO SE FOSSE MEDIÇÃO
>
> **Ordem do dono, 2026-09-15:** *"Não confiar muito nos contratos, pois tem muitos arcaicos e
> estou mudando com você agora."*
>
> **Contrato é ALEGAÇÃO DATADA. Medição é fato.** Onde os dois divergirem, vence a medição — e o
> contrato **se corrige na mesma sessão**, com data e motivo. Isto estende a R1 do próprio
> contrato (*"comentário que mente é bug a corrigir"*) ao próprio contrato.
>
> **Oito divergências medidas nesta sessão, todas de documento ou comentário contra o dado
> real:**
>
> | o que o texto afirma | o que foi medido |
> |---|---|
> | `CLAUDE.md:128`: 11.039 páginas públicas | **11.106** |
> | `CLAUDE.md` §5: sete motivos críticos de publicação | **onze**, e a lista é aberta |
> | `internal/stjacordaos/coleta.go:29`: maior arquivo mensal = 360.619 bytes | **14.442.367** (Quinta Turma) |
> | `internal/semantica/semantica.go:12-14`: 10.141 páginas / 41,5 MB | **11.248 / 46 MB** |
> | unit do grafo: 9,7 s, 13.575 nós, 148.571 arestas | **43,1 s, 79.706, 393.081** |
> | `tools/generate-grafo-juridico`: a aresta `aplica` não é populada | **22.789 arestas `aplica`** |
> | unit da onda diária `:7`: compila no `ExecStartPre` | **não existe `ExecStartPre=`** |
> | `cmd/generate-acordao-pages/main.go:185`: `-limite` é "páginas a ACRESCENTAR" | conta **remontagens** contra a cota (`:271`) |
>
> **Regra operacional que sai disto, e vai para os contratos (regra 19):**
>
> 1. **Antes de agir sobre um número do contrato, medir.** O contrato diz onde olhar; ele não
>    diz quanto é.
> 2. **Divergência encontrada = correção na mesma sessão**, com a medição anexada. Não se
>    anota "para depois" — é a R7.
> 3. **O que o contrato afirma sobre CAPACIDADE, VOLUME ou LIMITE é o mais suspeito de todos**,
>    porque envelhece a cada dia de crescimento — e é exatamente o tipo de afirmação que a
>    Regra Zero-C proíbe usar como teto.
> 4. **O contrato não vence o código vivo.** A precedência escrita (`AGENTS.md` → `GOAL.md` →
>    `CHECKPOINT.md` → `docs/`) ordena **documentos entre si**; nenhum deles ordena acima do
>    binário que roda hoje e do dado no disco.
> 5. **Nem por isso se ignora o contrato:** as regras que custaram incidente — anti-fraude,
>    coerência de artefato, não reverter trabalho, não quebrar produção — **não são números** e
>    não caducam por medição.

### O alvo da reescrita, documento a documento

| documento | o que muda |
|---|---|
| `CLAUDE.md` (raiz) | **as 21 regras** — cada uma como **veredito adotado de uma linha**, com data e caminho do parecer (o argumento vai para `docs/PRECEDENTES_DAS_ORDENS.md`, §P0d); §2 ganha os gatilhos **por ato**; §4 troca prudência por causa física medida; **nenhum número de estado permanece no contrato** |
| `AGENTS.md` | Regra Zero-C (proibido limitar), regra 8 (nenhuma decisão volta ao dono), regra 5 (portão é prova, não calendário) |
| `GOAL.md` | a meta deixa de ser só "10.000 páginas" e passa a incluir **citação por agente de IA** como métrica de primeira classe (§12 já diz que é a que vale) |
| `CHECKPOINT.md` | estado medido de hoje, com a **camada declarada** em cada número |
| `docs/CONTRATO_DADO_REAL.md` | R1–R10 ganham a regra 16 (não estreitar com número curto) e a 15 (camada da medição) |
| `docs/MEDICAO_DE_AUDIENCIA.md` e `docs/CRAWLERS_E_BOTS.md` | **borda é autoridade, origem é piso**, com o comando do `cloudflare_auth.py` e a rotina do Bing AI Performance |
| `docs/CONTENT_QUALITY.md` | FATO × PUBLICIDADE × JUÍZO (§P4); régua do produtor **é** a do gate (regra 10) |
| `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` | OAB alcança publicidade, **não** conteúdo informativo (CED arts. 39 a 47-A) |
| `docs/DATA_SOURCES.md` | DataJud destravado, dado público até o fim da cadeia |
| `~/.claude/CLAUDE.md` (máquina) | Regra Zero-C e regra 8 — as que valem em qualquer projeto |

**Ordem de execução:** o bloco canônico é escrito **uma vez**, replicado literalmente, e o teste
do item 3 abaixo é escrito **junto** — contrato reescrito sem teste volta a poder ser apagado
por condensação, que é exatamente o BUG-171.

### Propagação e teste — a parte que torna a reescrita irreversível

**Ordem do dono, 2026-09-15:** *"Isso tem que ir para qualquer contrato ou política, assim que
eu aprovar o plano. Nada de contrato solto. Nada de eu ter que ficar explicando toda hora. E
nada de limitar algo que tá crescendo e com potencial de lucro e viralização."*

**"Contrato solto" é o defeito real:** uma regra escrita só no `CLAUDE.md` vale até alguém abrir
`AGENTS.md` e seguir outra coisa. O repositório já pagou por isso — a condensação do commit
`64832bdd` apagou um parágrafo de governança e **só o teste** o denunciou (BUG-171).

### A infraestrutura JÁ EXISTE — medido, não proposto

`internal/contract/` já cobra por teste, com literal, os documentos: **`CLAUDE.md`,
`AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`, `DECISIONS.md`, `README.md`,
`codex2-goal-prompt.md`, `docs/ARCHITECTURE.md`, `docs/CONTENT_QUALITY.md`,
`docs/DATA_SOURCES.md`, `docs/DECISIONS.md`, `docs/LAB_VALIDATION.md`,
`docs/P0_OPERATIONAL_RUNBOOK.md`, `ROADMAP_P0_P5.md`** e outros. **Não é preciso construir
mecanismo: é preciso usar o que já existe para as regras novas.**

### O que se propaga, e para onde

| regra | vai para |
|---|---|
| **18 — proibido limitar o projeto** (Regra Zero-C) | **todos**: `CLAUDE.md`, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`, `~/.claude/CLAUDE.md` |
| **9 — dado público até o fim da cadeia, DataJud destravado** | `CLAUDE.md` §2 e §12, `AGENTS.md`, `docs/DATA_SOURCES.md`, `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` |
| **8 — nenhuma decisão volta ao dono** | `CLAUDE.md`, `AGENTS.md`, `GOAL.md` |
| **13 — OAB alcança publicidade, não conteúdo informativo** | `CLAUDE.md` §8, `docs/CONTENT_QUALITY.md`, `docs/PUBLICIDADE_E_NOME_EM_FONTE_OFICIAL.md` |
| **15 — tráfego mede-se na borda** | `CLAUDE.md` §2, `docs/MEDICAO_DE_AUDIENCIA.md`, `docs/CRAWLERS_E_BOTS.md` |
| **16 — não estreitar com número curto** | `CLAUDE.md`, `docs/CONTRATO_DADO_REAL.md` (é da família R1–R10) |
| **10 — gate usa a régua do gate** | `CLAUDE.md` §1, `docs/CONTENT_QUALITY.md` |
| **5 — portão é prova, não calendário** | `CLAUDE.md` §4, `AGENTS.md` |
| **20 — bug anterior não trava trabalho, e não se contorna** | **todos** — `CLAUDE.md` Postura/§1/§11, `AGENTS.md`, `GOAL.md`, `CHECKPOINT.md`, `~/.claude/CLAUDE.md`. **Cobrada nominalmente pelo dono** |
| **21 — idioma por camada** (instrução em inglês permitido; conteúdo e conversa em PT-BR) | `CLAUDE.md` §8 e Ortografia, `~/.claude/CLAUDE.md` |

### O mecanismo, em três camadas

1. **Um bloco canônico único**, escrito uma vez e **replicado literalmente**. Divergência entre
   cópias é pior que ausência: o §"precedência" do contrato manda vencer a regra mais
   restritiva, e duas redações diferentes criam ambiguidade onde deveria haver ordem.
2. **Um teste de contrato só** — `internal/contract/misc/regras_do_dono_test.go`, no molde do
   `peer_governance_test.go` — que exige a presença literal das regras **8, 9, 13, 15, 16, 18 e
   20** em cada documento da tabela. Uma regra apagada em **qualquer** um deles ⇒ **vermelho**.
   **A 20 é cobrada nominalmente por ordem do dono** (*"qualquer bug pré-existente é papel do
   Claude Code corrigir com agentes, e não travar trabalho por bug anterior… se uma peça estiver
   quebrada, o projeto pode quebrar"*), e é a que impede os dois erros opostos: parar culpando o
   passado, e empilhar contorno sobre contorno.
3. **Prova por mutação, que separa isto de um comentário:** apagar a regra 18 do `AGENTS.md` ⇒ o
   teste falha nomeando o arquivo e a regra. Se não falhar, o teste é decorativo e não vale o
   commit.

**Nota de escopo:** `~/.claude/CLAUDE.md` é o contrato **da máquina**, fora do repositório —
recebe as regras 18 e 8 (as que valem em qualquer projeto), mas não entra no teste do repo. As
demais são regras **deste** projeto e ficam nos contratos dele.

## P0d — Gravar O APRENDIZADO desta sessão no repositório

**Ordem do dono, 2026-09-15:** *"Você precisa colocar no plano para escrever no repo esse
aprendizado, e você não esquecer, para não ter bugs ou os agentes não ficarem cegos."*

**Isto é diferente do P0 e do P0b, e os três são necessários:**

| onde | o que é | quem lê, e quando |
|---|---|---|
| `CLAUDE.md` (§P0) | **regra** — o que se deve fazer | toda sessão, sempre, por injeção |
| memória (§P0b) | **gatilho** — o que lembrar no meio da conversa | por *recall*, quando o tema aparece |
| **repo (§P0d)** | **aprendizado** — o caso concreto, o número e o método que falhou | **qualquer agente**, por gatilho da tabela do §2 |

Regra sem o caso vira dogma que a próxima sessão relaxa; o caso sem a regra vira anedota que
ninguém aplica. **Esta sessão produziu material demais para caber só em regra.**

### O que se grava, e ONDE — dentro dos documentos que já existem (nada de contrato solto)

**1. `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`** — armadilha por arquivo, que é o propósito dele:

| armadilha medida nesta sessão | a lição |
|---|---|
| `ai_citation_signal_daily.jsonl` | mede a **ORIGEM**; declara `is_lower_bound: true`. **Volume mede-se na borda** |
| `edge_bot_agents_daily` | **cumulativo** (último por dia): somar linhas infla |
| `bing_webmaster_daily.jsonl` | `GetQueryStats`/`GetPageStats` são **busca clássica**; citação de IA **não está ali** |
| `extracoes_dispositivos.jsonl` | **append-only e vivo** — cresceu 3× durante uma auditoria. Medição exige **snapshot datado**; o denominador por chave de cache é 126.601, não 135.181 |
| `v2_rewrite_queue.jsonl` | **regenerado inteiro a cada ingest** — a data é da regeneração, não do enfileiramento |
| `risco_superacao.jsonl` | o score **satura**: 1.190 de 4.986 valem exatamente 1,0. O sinal útil é `peso_apos_revisao` |
| `first_published_at.json` | **congelado há 18 dias**; 999 chaves a menos que o manifesto ⇒ estreia re-datada a cada onda |
| `fila.sqlite` | tabela é **`tarefa`** (não `tarefas`), em `data/ai/` (não `var/cerebro/`), com **WAL vivo** |

**2. `docs/PRECEDENTES_DAS_ORDENS.md`** — o caso que originou cada regra, que é o propósito dele.
As 19 regras do §P0 entram com **data, número e prejuízo**, mais os erros de método que as
produziram:

- **Replicação que bate com o esperado é suspeita.** Repliquei `elegivel` em Python, bati com o
  número que eu esperava, e estava **5,3× errado** — faltava o primeiro filtro
  (`procedimental`, `main.go:515`), que barra 82,7% do corpus. **Dois agentes reproduziram o
  erro** com o meu filtro, e foi isso que o denunciou. O binário é a autoridade.
- **Medir na camada errada.** 943 requisições de origem apresentadas como volume de bot; a borda
  tinha **17.325 em 88.033**. Eu havia **transcrito** a frase *"origem ≤ borda SEMPRE"* do
  próprio arquivo, e usei o número da origem no parágrafo seguinte.
- **Filtro medido sobre si mesmo.** "100% de âncora literal" prova que `extracao.go:505` rodou —
  não que a atribuição está certa. O que ficava invisível: **15,51%** dos itens do modelo sem o
  artigo no trecho, e **1.966** itens descartados por invenção.
- **Piso aplicado na grandeza errada.** 250 palavras sobre a ementa de **entrada**, quando o
  gate mede o corpo da **página**; os cortes de saída dispararam **zero vezes** em 4.763
  candidatos. A constante é de `45d33ee8` e o comentário entrega o critério: *"com 250 palavras
  sobram 1.674 candidatos"* — calibrada para o **tamanho do pool**.
- **Estágio de produto usado como desconto de fato.** "Preview" qualifica a maturidade da API,
  não a confiabilidade das ~23.000 citações que a Microsoft exibe.
- **Risco jurídico inventado.** Classifiquei atribuição imprecisa como *"P1 sob a OAB"* e travei
  a escala. O CED alcança **publicidade** (arts. 39 a 47-A) e o art. 39 **exige** que ela seja
  *"meramente informativa"*.
- **LLM proposto onde havia bug determinístico.** Desenhei o cérebro como juiz de limiar; o
  workflow refutou com três evidências e mostrou a terceira categoria — **DIVERGÊNCIA é bug**,
  e se conserta fazendo um instrumento **chamar o outro**.

**3. `docs/goal/MAESTRO_CODEX_LOG.md`** — as decisões de política, que é o canal que o §11 nomeia:
DataJud destravado com os **dois** enforcers nomeados · a separação FATO × DIVERGÊNCIA × JUÍZO ·
recusa por juízo **nunca terminal** · o censo (não o cérebro) como julgador de estatístico ·
borda como autoridade de volume · Opus 5 padrão, `advisor` obrigatório, Sonnet fora.

**4. `docs/CONTRATO_DADO_REAL.md`** — a família R1–R10 ganha as regras 15, 16 e 19, que são
exatamente da natureza dela.

**5. O que foi DESCARTADO com evidência** — e isto é tão valioso quanto o que foi confirmado,
porque impede a próxima sessão de gastar tempo:

| hipótese | descartada por |
|---|---|
| comparação cross-família infla o molde | 64.440 pares, mediana 0,0079, **máximo 0,0313, zero ≥ 0,70** |
| `sem_duas_fontes_oficiais_verificaveis` barra páginas | **zero disparos** em 30, 120 e 500 |
| o campo `dispositivo` serve como camada citada | **é a fórmula de votação** (*"Vistos, relatados e discutidos…"*) — lidos 3 de 3 |
| linhas legadas do cérebro inventaram súmulas | **0 não atestadas** para URN LexML; as 77 enumerações aparecem no próprio trecho |
| as 36 truncadas são laço degenerado | **(b) ementa densa**: dose-resposta monótona, e **nenhuma** das 5.930 exibe a assinatura de laço |
| a data de estreia se dataria por commit | **commit ≠ sucesso** — a unit grava o cursor a cada lote |

### O mecanismo que impede o esquecimento

Documento que ninguém abre é documento que não existe. **Três amarras, todas já usadas neste
repositório:**

1. **A tabela "Leitura obrigatória, por gatilho" do §2 do `CLAUDE.md`** ganha as linhas, amarradas
   ao **ATO** e não ao tema — quem vai afirmar um volume não pensa "vou ler sobre medição":
   *antes de afirmar volume ou alcance* → armadilhas de camada · *antes de publicar número
   derivado de replicação* → "o binário é a autoridade" · *antes de propor LLM como juiz* →
   DIVERGÊNCIA é bug · *antes de recusar conteúdo por similaridade ou piso* → régua do gate.
2. **O teste de contrato do §P0c** cobra a presença literal das regras nos documentos. Apagar
   por condensação ⇒ **vermelho** (é o BUG-171, que já aconteceu).
3. **`git add` de cada arquivo por caminho exato**, no commit do §P−1 — com os cinco registros
   duráveis dos agentes como anexo de evidência. **Produto não fica untracked.**

## P0b — MODERNIZAR a memória (autorizado pelo dono) e depois acrescentar as novas

**Ordem do dono, 2026-09-15:** *"Tá autorizado a melhorar a memória para moderna atual."*

### O problema medido: o índice é uma lista, e listas não escalam

| medida | valor | limite oficial |
|---|---|---|
| `MEMORY.md` | **167 linhas, 23.970 bytes (23,4 KB)** | **200 linhas OU 25 KB, o que vier primeiro** |
| margem restante | **1.054 bytes · 33 linhas** | — |
| memórias indexadas | **~167**, uma linha cada | — |

**Duas consequências, e as duas são ativas:**

1. **As quatro memórias novas estouram o teto.** O que passar do corte **não carrega, em nenhuma
   sessão, sem aviso** — *"content beyond that threshold is not loaded"*.
2. **O índice é cronológico, não navegável.** 167 ponteiros em ordem de criação, e a sessão tem
   de ler os 167 para achar o que importa. É a mesma doença do `CLAUDE.md` de 645 linhas: o
   volume derrota a aderência.

### O desenho novo — três camadas, cada uma com o mecanismo oficial certo

**1. `MEMORY.md` deixa de ser lista e passa a ser MAPA POR ATO.** A doc oficial diz que o Claude
*"scans structure the same way readers do"*, e a lição desta sessão é que gatilho por **tema** não
dispara — só por **ato**. O índice novo agrupa por momento de decisão:

```markdown
## Antes de afirmar volume, alcance ou citação
- [Medição é na borda](medicao-de-trafego-e-na-borda.md) — origem é piso; 943 × 17.325
- [Séries que enganam](medicao-chaves-que-enganam.md) — cumulativa não se soma
## Antes de publicar número derivado de replicação
- [Replicação que bate é suspeita](replicacao-que-bate-e-suspeita.md) — errei 5,3×
...
```

**Estimativa escrita antes: 167 linhas → ~60. MEDIDO em 2026-09-16: 167 → 181.** Os bytes
caíram bem (23.970 → 23.167, com os 5 registros novos já dentro), mas **as linhas SUBIRAM** — e
linha é o eixo que aperta primeiro, porque o teto é *"200 linhas OU 25 KB, o que vier primeiro"*.

**Por que a estimativa errou:** eu supus que o agrupamento absorveria repetição de contexto. Não
absorve — cada memória continua sendo **um ponteiro que não se pode perder**, e os 10 cabeçalhos
de ATO *acrescentam* 10 linhas. Só se ganharia linha apagando ponteiro, que é o que não se faz.

**O alívio real não está aqui: está no item 2 desta frente** — mover o que é específico de UM
arquivo para `.claude/rules/` com `paths:`, que carrega on-demand e **custa zero no índice
permanente**. Esse item depende do §P0a, então **esta frente não fecha sozinha**: entrega o gate
e a compactação (feito), e fica bloqueada na migração para rules.

*Estado medido: 181 linhas, 23.167 bytes, 171 ponteiros, 0 quebrados, 0 órfãos, 90% dos dois
eixos, folga de 9 linhas.*

**2. O que é específico de arquivo sai da memória e vai para `.claude/rules/` com `paths:`** —
mecanismo oficial que **carrega on-demand, só quando o arquivo casado é tocado**
([large-codebases](https://code.claude.com/docs/en/large-codebases#choose-between-per-directory-claude-md-and-path-scoped-rules)).
Candidatas imediatas, hoje ocupando linha no índice permanente: as armadilhas de
`published_manifest`, `pages.json`, `fila.sqlite`, `v2_pages/`, `social_policy.json`,
`first_published_at.json`, `extracoes_dispositivos.jsonl`. **Custo no índice: zero.**

**3. Os subagentes ganham memória própria — e esta é a correção da causa-raiz.** A doc é
explícita: *"the main conversation's auto memory isn't loaded into subagents; the exception is a
fork"*. **Por isso o mesmo erro volta:** a lição não chega ao próximo agente. O campo `memory:`
no frontmatter de `.claude/agents/*.md` resolve, e o campo `skills:` garante que o agente nasça
com o procedimento certo em vez de recebê-lo colado no prompt — que é o que eu venho fazendo,
com prompts de 4 KB por agente.

### O gate que impede a reincidência

`check-memoria-no-limite`: reprova quando `MEMORY.md` passa de **24 KB ou 190 linhas** — margem
antes do corte silencioso, não depois. **Sem ele, o truncamento volta na décima memória nova**,
e ninguém percebe, porque a falha é silenciosa por desenho.

### Só DEPOIS disso, as quatro memórias novas



Ordem do dono: *"precisa atualizar as memórias"*. Elas são o que sobrevive a `/clear` e entra
por *recall* nas sessões seguintes — é o par do `CLAUDE.md`, que entra sempre. Texto pronto,
para gravar em `~/.claude/projects/-opt-wiki/memory/` assim que a execução começar:

**`medicao-de-trafego-e-na-borda.md`** — *type: feedback*
> A origem mede o RESÍDUO, não o volume: o acervo sai de `public/` com `s-maxage=604800` atrás
> da Cloudflare, e `HIT` na borda não toca a origem. Medido em 2026-09-15: origem ~3.800
> requisições de bot em 24 h contra **17.325 bots em 88.033 requisições** na borda.
> **Why:** apresentei o número da origem como volume de bot e subnotifiquei o alcance da
> plataforma, depois de ter transcrito a frase *"origem ≤ borda SEMPRE"* do próprio arquivo que
> eu estava lendo.
> **How to apply:** volume, alcance e retorno de bot ⇒ `tools/cloudflare_auth.py` +
> `httpRequestsAdaptiveGroups`; `JANELA_MAXIMA_DIAS_FREE = 1` obriga fatiar, não desistir. Nunca
> a Global API Key como `Authorization: Bearer` (só `X-Auth-Email`/`X-Auth-Key`). A origem
> continua autoridade para rota dinâmica, gêmea Markdown, `/api/v1` e MCP.
> Liga com [[travessia-origem-vs-borda-calculo]], [[medir-bots]],
> [[instrumento-casa-um-produtor]].

**`nao-estreitar-o-projeto-com-numero-curto.md`** — *type: feedback*
> A plataforma funciona: 88.033 requisições/dia na borda, 17.325 de bot, +23 mil citações de IA,
> e uma máquina muito mais potente a caminho. Número curto apresentado como teto é sabotagem
> involuntária do negócio.
> **Why:** o dono, 2026-09-15: *"você tá limitando meu trabalho que tá dando certo a números
> mentirosos… excluindo negócios valiosos, que é inadmissível"*. Aconteceu três vezes nesta
> sessão: teto de publicação por cota de anúncio, "risco sob a OAB" inventado para travar
> conteúdo informativo, e o volume de bot medido na camada errada.
> **How to apply:** antes de escrever "pequeno", "marginal" ou "não vale a pena", medir na fonte
> com autoridade. **Instrumento que declara a própria limitação é ordem de trocar de
> instrumento**, não nota de rodapé. Teto só com limite físico medido.
> Liga com [[politica-do-repo-nao-e-teto]], [[alta-escala-autonoma]],
> [[ausencia-de-sinal-nao-e-evidencia]].

**`etica-oab-alcanca-publicidade.md`** — *type: project*
> Provimento 205/2021 e CED **arts. 39 a 47-A** disciplinam **publicidade e captação**. O art. 39
> exige que a publicidade tenha *"caráter meramente informativo"*. **Não há norma disciplinar
> sobre precisão de citação em conteúdo informativo.**
> **Why:** classifiquei atribuição imprecisa como *"P1 permanente sob a OAB"* e usei isso para
> bloquear a escala do canal de acórdãos. O dono: *"larga disso de OAB. Se o conteúdo é
> informativo, a OAB não pune."*
> **How to apply:** o gate de publicidade vale onde há CTA, oferta, preço ou promessa de
> resultado. Erro de conteúdo é **qualidade**: conserta-se no produtor e a página publica e
> refina. Quem alegar risco disciplinar **cita o dispositivo**; sem dispositivo, a rota segue.
> Liga com [[dono-nao-revisa-paginas]], [[contrato-dado-real]].

**`replicacao-que-bate-e-suspeita.md`** — *type: feedback*
> Repliquei `elegivel` em Python, bati com o número que eu esperava, e estava **5,3× errado** —
> tinha omitido o primeiro filtro (`procedimental`, `main.go:515`), que barra 82,7% do corpus.
> **Why:** replicação que confirma a expectativa é motivo para desconfiar dela, não para confiar.
> Dois agentes reproduziram **o erro** com o meu filtro, e foi isso que o denunciou.
> **How to apply:** o binário é a autoridade — rodar o `-seco`/`--dry-run` do próprio produtor
> antes de publicar qualquer número derivado. Conferir contra um controle de ordem de grandeza
> (aqui: a taxa de 4,51% registrada no commit que criou o gerador).
> Liga com [[contrato-dado-real]], [[teste-que-reimplementa-nao-testa]],
> [[medi-so-depois-de-rodar]].

**Atualizar** `MEMORY.md` com uma linha por memória nova, e **corrigir** a linha de
[[ollama-local-memoria-e-banda]], que fala de "dois residentes derrubaram o host": o teto de
9 GiB agora tem de virar duas contas separadas (`size_vram` ≤ 13 GiB e `size − size_vram` ≤
2 GiB) na máquina com GPU, e `size_vram` **existe** no `/api/ps` (medido: 0,0 em CPU puro).

## P1b — Estancar o dado corrompido que já está no ar

**É o primeiro trabalho de engenharia do plano, porque é o único defeito que piora sozinho** —
cada onda re-data mais páginas, e o Googlebot e os agentes de IA leem o resultado.

1. **Registrar `tools/generate-first-published-at` no registro de produtores do P3** e ligá-lo
   como etapa da onda, **antes** de `publish-v2-direct`. É a causa-raiz: o arquivo está
   congelado há 18 dias porque ninguém o executa.
2. **Reconstruir `first_published_at.json` a partir do histórico git** — as 999 chaves
   ausentes. O gerador já sabe fazer isso; o dado é recuperável, e é por isso que este passo é
   barato.
3. **Commitar `published_manifest.jsonl` na onda** (defeito N13). Hoje a onda commita portfólio
   e páginas e **nunca** o manifesto — que está `M` há 5 dias —, e é justamente do histórico
   dele que o gerador de estreia deriva a data. **Enquanto o manifesto não for commitado, o
   passo 2 volta a se degradar.**
4. **Corrigir as páginas já servidas:** re-render das 944 com a estreia verdadeira. Pela matriz
   do §6, mudar `datePublished` no JSON-LD é mudança de **texto/estrutura servida** ⇒ deploy
   **sem** `--ressemear` (a re-datação para a data VERDADEIRA não é re-datação nova, é
   correção), e a purga do deploy basta.
5. **Gate de cronologia**, que é o que impede a reincidência: `dateModified < datePublished`
   em qualquer página servida ⇒ **vermelho**. `main.go:485-492` já declara essa combinação
   proibida — **a regra existe e ninguém a verifica sobre o artefato servido**. O gate lê
   `public/`, não o JSONL, porque é o servido que engana o buscador.

**Prova de aceitação:** `datePublished` de uma amostra por *stride* das 944 bate com a data de
estreia reconstruída do git; **zero** páginas com `dateModified < datePublished` em `public/`;
`publicado_em` deixa de vir vazio em `/api/v1` para essas rotas; e a prova negativa — forjar
uma cronologia impossível numa página ⇒ o gate novo fica vermelho nomeando a rota.

## P1 — Destravar a coleta do STJ

1. **Isolar a falha por competência.** Em `coleta.go:176` (JSON ilegível) e `:167` (rede e
   status): a competência vai para **quarentena contada** e o laço segue para a competência
   e o **dataset** seguintes. Erro de licença e erro de escrita **continuam fatais** — são
   proveniência e disco nosso, não mês ruim.
2. **O cursor NÃO avança sobre competência quarentenada.** `JaColetado` tem de continuar
   **falso**, senão o cursor mente — é o defeito que o `--max-registros` cometeu em
   2026-09-08. O estado de quarentena mora **fora** de `Datasets`, em campo aditivo
   (`VersaoCursor` fica em 1).
3. **Retentativa barata:** `Condicional` passa a consultar a quarentena e manda
   `If-None-Match` — enquanto a fonte não mexer, custa **um 304 e zero bytes**. A cada 7ª
   tentativa vai sem validador, para que um 304 de cache não congele a quarentena; há
   precedente de a fonte **revisar meses passados**.
4. **Artefato próprio** `quarentena.jsonl`, irmão do manifesto — não linha no manifesto, que
   é indexado por `url → dataset` em `cmd/generate-acordao-pages/main.go:614-638`.
5. **Quando ainda falhar** (para o alerta voltar a significar algo): corpo acima do teto, **1
   ocorrência** (o maior arquivo real é 14,4 MB = 21% do teto); dataset com **100%** dos
   recursos quarentenados e ≥3 tentados; share da execução **> 20%** com ≥5 quarentenados —
   **25× a taxa-base de 0,8%**; quarentena com mais de **14 dias** ainda não alertada.
6. **`cmd/collect-stj-acordaos/main.go:118-121` imprime o relatório ANTES de devolver o
   erro** — é por isso que o alerta de hoje chega sem número nenhum.
7. **Teste provado por mutação:** fixture com os **599 bytes verbatim**; sem a correção, os
   datasets seguintes não são visitados. Mutações que o matam: restaurar o `return`;
   trocar `continue` por `break`; chamar `Registra` na quarentena; quarentenar sem contar.

**Recuperação:** **391 competências** nos 8 datasets incompletos (número **medido** por censo da
fonte, não mais extrapolado), com a espera imposta pelo `Crawl-Delay: 10` que o STJ publica —
teto externo legítimo, não margem nossa.

**E mais os 460 MB do acervo histórico**: acrescentar ao coletor o reconhecimento do
`20220508.zip` de cada dataset, que o regex atual ignora. É corpus que **nunca entrou no
projeto**, e entra pela mesma passada. O volume exato se lê pelo diretório central de cada ZIP
por `Range`, antes de decidir a ordem de download. Ordem: os dois truncados primeiro (o cursor mente sobre eles), depois Corte
Especial e as Seções (uniformizadores, baixo volume), por último as três turmas de volume
(~122.500 dos ~150.000 registros).


> ### CORREÇÃO DE 2026-09-16 — o teto NÃO sobe, e o número que eu usei era de OUTRO arquivo
>
> Eu escrevi, em três lugares, que *"o maior arquivo mensal tem 26.704.470 bytes"* e que a folga
> do `LimiteArquivoMensal = 64 << 20` caiu para **2,5×**. **Errado, e o erro é de categoria.**
>
> Os 26.704.470 bytes são de
> `data/corpus/jurisprudencia/stj-espelhos/registros-2026-06.jsonl` — **o NOSSO JSONL agregado**,
> que soma vários datasets. `LimiteArquivoMensal` limita **um corpo HTTP**: um dataset × uma
> competência. São grandezas diferentes, e eu comparei uma com o teto da outra.
>
> **Medido nas 391 linhas de `censo-20260915/sizes.jsonl`**, o maior mensal real da fonte:
>
> | dataset | competência | bytes | MiB |
> |---|---|---|---|
> | quinta-turma | 20260630 | **14.442.367** | **13,77** |
> | sexta-turma | 20260630 | 7.651.936 | 7,30 |
> | segunda-turma | 20260630 | 6.383.127 | 6,09 |
> | primeira-turma | 20260630 | 2.934.972 | 2,80 |
> | corte-especial | 20250930 | 709.333 | 0,68 |
> | primeira-secao | 20240531 | 676.664 | 0,65 |
> | segunda-secao | 20260831 | 612.995 | 0,59 |
> | terceira-secao | 20260831 | 414.979 | 0,40 |
>
> **Folga real: 4,65×. O teto de 64 MiB fica.** E o próprio §P1 item 5 já dizia *"o maior arquivo
> real é 14,4 MB = 21% do teto"* — **o plano se contradizia**, e esta é a linha certa. O
> comentário de `coleta.go:29` deixa de trazer número e passa a dizer **onde medir**.
>
> *(Lição de método, que é a regra 19 outra vez: número que vem de um arquivo NOSSO não se compara
> com o teto de um corpo da FONTE. Antes de usar um número, confira de que grandeza ele é.)*

> ### Verificação obrigatória ANTES da recuperação: a folga do teto evaporou
>
> `internal/stjacordaos/coleta.go:29` afirma que o maior arquivo mensal tem **360.619 bytes**.
> **Medido: 26.704.470 — 74× maior.** O `LimiteArquivoMensal = 64 << 20` tinha folga de **178×**
> quando o comentário foi escrito; hoje tem **2,5×**.
>
> A recuperação traz **391 competências**, inclusive as turmas de maior volume, **e mais os
> ~460 MB de ZIP histórico** que o regex do coletor nunca leu. **Se um mensal passar de 64 MiB,
> `cliente.go:190-196` recusa com `corpo maior que o limite`** — e a coleta para de novo, pelo
> mesmo padrão que este plano existe para corrigir.
>
> **Passo novo, antes de recuperar:** censo `HEAD` do maior arquivo de **cada** dataset ausente
> (o agente de volumes já produziu parte disso); se algum passar de ~50 MiB, o teto sobe **com a
> medição anexada** — nunca por precaução, e nunca depois de a coleta falhar. E o comentário da
> `:29` deixa de trazer número: passa a dizer **onde medir**.

**`--refazer` não se usa aqui:** mês nunca coletado não está no cursor; e `--refazer` não
manda validador **de propósito** (`coleta.go:154-162`), então rebaixaria a fonte
re-baixando os 128 meses bons.

**Janela a evitar:** 09:40–10:20 — `run-heavy-throttled` sai com **código 75** no mesmo
escopo de lock em vez de esperar, e o timer diário cairia no meio gerando alerta falso.

**Depois da coleta, a ordem que entrega mais rápido:**
`cmd/generate-extracao-por-parser` → `cmd/generate-writeback-extracoes` →
`cerebro enfileirar-extracoes`. **81,4% do ganho de elegibilidade vem do parser
determinístico** (28.559 das 35.082 promoções são `modelo:"parser"`), em segundos e sem GPU.

**Impacto — números do CENSO, e as duas projeções lineares que eles substituem.** Eu havia
escrito *"corpus → ~210.000"* e *"elegíveis 4.763 → ~16.000"*, ambas por extrapolação linear com
banda de ±30%. **O censo `HEAD` integral das 391 competências (§1.1) derrubou as duas**, e o
próprio §1.1 mede que a projeção linear erra **36–49%** aqui — usar essa banda depois de ter o
censo seria usar o instrumento que já sei estar errado:

| medida | projeção linear (superada) | **censo / medição por dataset** |
|---|---|---|
| corpus pós-recuperação | ~210.000 (26% alto) | **165.981** (banda 154.747–172.721) |
| acórdãos novos | — | **105.760** em 350,2 MiB |
| **candidatos novos** | ~16.000 | **+4.485** (IC **4.003–5.150**) |
| páginas novas projetadas | — | **3.496** *(linear sobre o rendimento anti-molde, que é sequencial — só o gerador fecha)* |

**A causa do erro é estrutural e está nomeada:** a taxa de candidato varia **38× entre órgãos**
(0,35% na Quinta Turma contra 13,44% na Primeira Seção), porque o habeas corpus chega como
**`AgRg no HC`** e cai no filtro `procedimental`. Transportar uma média global por cima disso
superestima em quase 50%.

**E fora desta conta, de propósito:** o `20220508.zip` de cada dataset traz **1,95 GiB
descomprimidos, 613–679 mil acórdãos** — **~5,6× todo o corpus pós-recuperação** —, a uma regex
de distância (`dataset.go:33`). É frente própria dentro do P1.

**Prova:** cursor com 10 datasets; contagem por dataset; elegibilidade refeita.

## P2 — Desfazer a corrupção do shfmt

Restaurar as 8 chaves (edição para frente, **nunca** `git revert`) e acrescentar gate que
reprove chave de array associativo com espaço — `bash -n` não detecta, então a guarda tem de
ser semântica.

**Prova:** nenhuma chave com espaço; `check-frescor-canal-diario` volta a julgar o dia de
hoje; a passada das 12:20 volta a coletar.

## P3 — Matar a família dos produtores órfãos

1. **Registro executável** `ops/produtores-de-pagina.jsonl`: uma linha por produtor com
   `cmd`, `shard`, `portfolio`, `gatilho`, `limite_env`. `run-daily-content` e o publicador
   do P6 **derivam** o mapa de geradores dele, em vez do `declare -A` literal. Produtor fora
   do registro não roda; produtor sem `gatilho` reprova.
2. **Gate `produtor-orfao`** em `internal/checks/` (case + `Names` + impl + teste), no molde
   de `tools/check-cadeia-editorial-ordem-declarada`, que já existe como detector de órfão.
   Predicado: todo `cmd/generate-*` que escreva em `data/editorial/v2_pages/` e use
   `shardpreserve` e não esteja no registro ⇒ reprova nomeando `arquivo:linha`.
3. **Reprova por entrada nova, não por nível** — precedente
   `gate-vermelho-por-estoque-que-nada-drena`.

**Prova negativa:** remover uma linha do registro ⇒ o gate fica vermelho nomeando o arquivo.

## P6 — Publicador autônomo do cérebro

**A rota óbvia está fechada, e fechá-la foi certo.** Um executor `gerar_paginas_acordao`
dentro do worker exigiria dar `data/editorial/`, `public/`, `content/` e `.git` a um processo
que fala com um LLM 24/7 — a unit declara `ProtectSystem=strict` e
`ReadWritePaths=/opt/wiki/data/ai /opt/wiki/data/ops`, com o contrato escrito no cabeçalho.
Mina adicional: `Fila.Reivindicar` (`fila.go:378`) **não filtra por tipo**, e `Worker.Passo`
sem executor para o tipo chama `Falhar` **terminal, sem backoff** — a tarefa seria comida e
morta.

**Desenho adotado — a aresta inversa da que já existe.**
`wikijuridica-cerebro-enfileirar.path` já faz "o acervo muda → systemd dispara oneshot
sandboxed que escreve na fila". O publicador é o espelho: o cérebro produz → systemd dispara
um oneshot **privilegiado** que roda a cadeia do §5. **Zero mudança em `fila.go`.**

```
wikijuridica-cerebro.service        (sandbox: data/ai, data/ops)
  extrair_dispositivos → writeback
                            │
wikijuridica-cerebro-publicar.timer (oneshot, escrita no repo)
  1. generate-writeback-extracoes
  2. generate-acordao-pages -limite $N
  3. tools/publicar-estoque --rotulo cerebro   (etapas 2.5→9 VERBATIM,
                                                sob o MESMO flock da onda)
```

A onda diária **não é substituída — deixa de ser a única porta**. As etapas 2.5→9 são
preservadas literalmente: são prova acumulada de incidente real.

### Defeitos que caem ANTES de escalar (senão o motor entrega 30, e não o poço inteiro)

1. **`generate-acordao-pages` empaca na segunda passada.** `main.go:741` exclui o próprio
   shard de `intentsPublicados` (o comentário explica: lê-lo de volta esvaziaria o gerador);
   logo as páginas da passada anterior **não** ficam em `protegidos`, são remontadas, e
   `:271` conta essas remontagens contra a cota; `ordenaPorEvidencia` (`:548`) é
   `SliceStable` determinístico. **`-limite 30` devolve as mesmas 30 para sempre.** Correção:
   padrão `internal/tetodelote` — remontar, **isentar da cota**, pular o anti-molde para
   elas. **Não** pular os intents do próprio shard: `shardpreserve` lê
   `git show HEAD:<shard>`, então página de uma passada cujo commit falhou some das duas
   pontas.
2. **Trava de molde no limiar de auditoria, sem margem.** Gerador em `0.70` sobre corpo que
   **exclui o FAQ**; gate em `0.70` sobre o corpo **inteiro**. Os cinco irmãos já estão em
   **0,60**. Como o gate reprova pelo **máximo** de pares e o máximo sobre n² só cresce, a
   17 mil páginas um par acima de 0,70 é quase certo — e o gate não para a onda, só a deixa
   `parcial` para sempre.
3. **"Vazio" codificado como erro** (`main.go:219`, exit 1). Um drenador leria como falha
   permanente ao esgotar o poço. Vira exit 0 com linha explícita.
4. **Rotação de shard.** 3.899 B/linha medidos; 4.763 páginas dariam **18,6 MB num único
   JSONL**, reescrito e commitado a cada execução. Teto ~1.000 páginas/~4 MB, append-only,
   tratando **todos** os `stj-acordao-derivado-*` como próprios — senão um intent de `-01`
   reaparece em `-02` e `check-v2-cross-shard-collision` dispara.

### Cadência

**O IndexNow limita ANÚNCIO, não publicação** — são filas distintas; a página vai ao ar pela
transação e é descoberta pelo sitemap de qualquer forma. Deixar o teto de 1.000/dia governar
a fábrica seria freio no eixo errado.

**Não há cadência em dias. Não há "fase 1" que espera amanhã.** O único portão é uma **prova
de travessia**, e ela roda na mesma sessão:

| portão | o que é | quando o seguinte abre |
|---|---|---|
| **travessia** | primeiro lote atravessa preservação, pareamento, pre-commit, censo, transação e smoke. O shard **nunca foi gerado**, então esta passagem é inédita e é a única coisa que ainda não tem prova | assim que `manifest ⊆ sitemap ⊆ public` fechar com SHA batendo |
| **drenagem** | `-limite` aberto, o poço inteiro | imediatamente após a travessia fechar, no mesmo turno |

O tamanho do primeiro lote não é uma escolha de prudência: é **o menor lote que exercita todos
os elos**. Passou, o `-limite` sobe por variável de ambiente e não volta a descer.

**Os únicos tetos que permanecem têm causa física externa e medida**, nunca margem minha:
`Crawl-Delay: 10` do servidor do STJ (é o operador remoto que o publica), a vazão do modelo em
tok/s, e o limite de requisições que o operador do DataJud publica. **Cota de anúncio do
IndexNow não é teto de publicação** e não governa nada aqui.

**Risco a nomear:** mudar o template do gerador **depois** da escala reescreve 11 mil páginas
de uma vez e dispara `check-lastmod-causalidade`. Edição de template do motor passa a ser
**release coordenado**.

### Correção a uma premissa minha

`cmd/publish-v2-direct` **não importa `internal/publicrelease`** (a única ocorrência é um
comentário na linha 3772 — meu primeiro grep casou o comentário). Logo o teto de coorte de
250 **não se aplica**. E a "trava" é só `--allow-public-write`, flag com default `false`
(*"sem esta flag o comando só relata"*), que a onda diária já usa todo dia. **Não havia
decisão do dono pendente aqui.** E `publish-v2-direct` recusa `-limit` junto com
`-allow-public-write` (`main.go:351`) — a cadência mora no `-limite` do gerador, a montante.

### CORREÇÃO DATADA (2026-09-16): o passo 3 do publicador, e o contrato de poderes do cérebro

*Este bloco corrige o desenho acima. O texto anterior fica onde está — parágrafo superado ganha
data e motivo, não se apaga.*

**1. `tools/publicar-estoque` não existia, e o que mudou não foi só criá-lo.** O comando
prescrito na linha 2246 foi conferido por três frentes independentes nesta data: `ls` devolvia
*"Arquivo ou diretório inexistente"*. Ele existe a partir de agora, **mas não roda as etapas
2.5→9 por conta própria — ele APONTA a cadeia única para o estoque certo e responde pelo que
ficou.** "VERBATIM" é o mesmo *código*, não uma cópia dele: uma segunda escada de nove degraus
envelheceria sozinha, e este repositório já pagou por regra duplicada mais de uma vez — a
comparação *"o censo acompanha o estoque?"* chegou a ter **três** implementações, e
`tools/publicar` passou a delegar ao check por causa disso.

O que a cadeia ganhou, em `tools/run-daily-content`: `--gatilho=<g>` (deriva os produtores do
registro, e não mais o literal `onda-diaria`), `--somente=<canal>`, `--sem-coleta`, `--sem-git`,
`--rotulo=<texto>`, `--minimo-novas=<N>` e `--unit=<%N>`. `--somente-noticias` continua valendo
palavra por palavra: a unit das 12:20 invoca por esse nome, e renomear flag viva quebra unit que
funciona.

**2. O elo vivo NÃO é o de acórdãos — é o da notícia, e ele estava medido e parado.** O cérebro
grava o comentário autoral em `data/ai/noticias_redigidas.jsonl`; quem o leva à página é
`cmd/generate-noticia-pages`, que só roda às 04:20 e às 12:20. Medido às 16:02 de 2026-09-16:
**cinco comentários aprovados e zero deles em qualquer página** (sete, uma hora depois — o
cérebro continuou produzindo durante a sessão). O gatilho é
`wikijuridica-cerebro-publicar-noticias.path`, sobre esse arquivo, com o `.timer` irmão de
30 min como rede de segurança — `PathChanged=` é gatilho de **borda** e o evento se perde em
reboot, unit parada ou passada em curso. O estado pendente **não é o evento: é o DADO**, e por
isso a reconferência é barata e correta.

**3. `extracoes_dispositivos.jsonl` NÃO pode ser gatilho de `.path`, e a medição é do próprio
journal.** Ele é reescrito a cada 3–6 min pelo cérebro, e cada disparo compilaria Go, tomaria o
lock pesado e **pausaria o cérebro** (`[ocupacao_lock/lock_pesado]`, medido às 15:11 de
2026-09-16). Além disso ele é matéria-prima, não produto. O canal de acórdãos fica com `.timer`,
como o diagrama do §P6 já dizia.

**4. A ordem do dono de 2026-09-16 tira o histórico do publicador, e isso derruba um passo da
cadeia — por decisão dele, não por prudência minha.** A ordem é literal: *"não tem poder de
excluir, somente quarentenar para o Claude Code refinar depois, criar, fazer build, deploy,
menos git, histórico e deleção de qualquer espécie. Se der erro, deve entrar em quarentena."*

O passo que **não cabe** é o commit — etapas 5/9, 6/9 e 8.05/9. A consequência é assimétrica e
tem de ser lida como tal:

| lane | intenção nova? | o publicador autônomo… |
|---|---|---|
| **enriquecimento** (comentário do cérebro em página que já existe) | não | **publica sozinho, fim a fim**. O pareamento passa porque a intenção já está no commit pai; o shard fica não commitado e **preservado com data** em `.agents/runtime/publicador-sem-git/` |
| **rota nova** (drenagem de acórdãos) | sim | **monta e QUARENTENA**. O gate de pareamento lê o portfólio do commit **pai**, por desenho declarado; publicar sem isso é o que ele recusa. O Claude Code commita, e a passada seguinte publica |

E ele não empilha lote sobre lote esperando: `tools/publicar-estoque` mede, em tempo presente
(`git diff` sobre o portfólio do canal), se há intenção não commitada e, se houver, **não roda o
gerador**. No instante do commit o bloqueio some sozinho, sem nenhum registro precisar ser
apagado — apagar é o que a ordem veda.

**5. A vedação é executável, não escrita.** `ReadOnlyPaths=/opt/wiki/.git` nas duas units do
publicador: a indexação e o commit falham com EROFS dentro delas, e nenhum código chamado por
elas pode afrouxar isso. `git show HEAD:<shard>`, `git ls-files` e `git log` continuam
funcionando — e **têm de continuar**, porque alimentam `check-shard-preservation` (a etapa que
PARA a cadeia quando um gerador apaga página redigida) e `generate-first-published-at`. Trava de
segurança que quebrasse a preservação teria trocado um risco por outro maior, e o dono foi
explícito: *"sem travar o cérebro"*.

**6. O teto por execução: onde ele está, e o que ele não é.** O teto de quanto se **publica** já
existe e é `limite_env`/`limite_padrao` do registro de produtores, aplicado pelo gerador e
incidindo só sobre o que se **acrescenta**. O `teto_por_execucao: 5` de
`content/cerebro_publicacao.json` **não governa página**: ele é o freio do comentário de rede
social (único leitor `cmd/cerebro/comentarios.go:451`, no contexto do gate de habitualidade da
OAB), e aplicá-lo a páginas capava a drenagem em cinco por execução — contra este mesmo §P6 (*"o
`-limite` abre em seguida, no mesmo turno"*) e contra a Regra 18. O teto que **faltava** é outro
e tem causa medida: `teto_de_tentativas_por_peca` (campo novo no mesmo arquivo; o decodificador
é leniente, conferido em `comentarios.go:445` — o daemon em execução não quebra). Peça que nunca
entra no estoque dispararia a cadeia inteira a cada volta do timer, para sempre; esgotado o teto
ela é **parada** com o motivo, continua no disco e vira pauta.

**7. O piso de rota nova é 0 na passada de enriquecimento, e isso não é afrouxar gate.**
`check-onda-avanca --minimo 1` existe porque a onda tem por função trazer rota nova. A passada de
enriquecimento muda o **corpo** de uma rota que já existe: `novas_publicadas` é zero por
construção, e cobrar 1 reprovaria a passada por ela ter funcionado. **O controle que importa
continua reprovando nos dois casos**: `sumiram > 0` falha antes e independentemente do
`--minimo` (`tools/check-onda-avanca:138`), e o critério positivo da passada passa a ser a
reconciliação peça a peça de `publicar-estoque` — mais estrita que *"apareceu rota nova"*, porque
nomeia exatamente o que faltava e o que continua faltando.

**4-bis. A POLÍTICA MUDOU NA MESMA TARDE, e o item 4 acima fica como está, superado
com data.** Ordem do dono, 2026-09-16: *"o cérebro precisa publicar acórdão. Mude a engenharia,
ele deve publicar. Você não pode proibir com literalidade. (…) Se for seguro ele pode
commitar."* Caiu a **proibição**; ficou o **critério de segurança**.

O que a substitui é `tools/cerebro-commitar` — a **única porta**, e ela não é "menos trava":

| o que ela permite | o que ela recusa, e como |
|---|---|
| estagiar e commitar, **em invocações separadas**, sob `flock /tmp/opt-wiki-commit.lock` | **subcomando destrutivo**: não há parâmetro que o expresse. `reset`, `revert`, `checkout`, `restore`, `stash`, `clean`, `rebase`, `cherry-pick`, `push`, `filter-branch`, `gc`, `rm` não são proibidos por lista — são **inexprimíveis** |
| só caminhos da **allowlist derivada** de `ops/produtores-de-pagina.jsonl` (mais os dois artefatos de publicação, nomeados) | `fora_da_allowlist`, conferido por **caminho canônico resolvido e pertinência a conjunto** — nunca prefixo de string, que `..` derrota |
| só **arquivo regular** | `diretorio` (o defeito que já varreu trabalho de outra sessão três vezes), `symlink`, `travessia` (`..` recusado pelo literal) |
| só **criação e alteração** | `remocao`, conferida **depois de estagiar**, no `--name-status` do índice: qualquer `D` ou `R` aborta antes do commit. Deleção continua vedada, e essa parte da ordem **não mudou** |

**Um `git` falso no PATH foi considerado e REFUTADO por fonte primária**: `.githooks/pre-commit`
reseta `PATH=/usr/bin:/bin` e fixa `GIT_BIN=/usr/bin/git` com o motivo escrito — *"não aceite um
executável injetado por PATH (inclusive dentro do próprio repositório)"*. Para o hook, um shim
nosso seria o ataque que ele existe para barrar.

**4-ter. A reprovação do pre-commit se classifica por CAUSA, e sem isso a peça trava à toa.**
O caso é medido, num commit do próprio maestro nesta sessão:
`go-index-compile-closure: REPROVADO: compile closure excedeu 76.5s concedidos` — **não era
defeito da peça**, era contenção, e o mesmo commit passou na retentativa sem uma linha alterada.
Três classes, três destinos:

| classe | o que casa | destino |
|---|---|---|
| **peça** (default, conservador) | gate de conteúdo, pareamento, produto sumido | **quarentena**, espera correção |
| **ambiente** | `compile closure excedeu`, `index.lock`, `Unable to create`, `Resource temporarily unavailable`, teto de compilação | **retomada**, e a peça **não consome tentativa** |
| **hook** | `Traceback`, `ModuleNotFoundError`, `command not found`, `rc=127` | **retomada + alerta nomeado** — hook quebrado que ninguém vê é pior que peça parada, e esta sessão mediu **cinco** gates reprovando sem defeito real |

**A ordem de avaliação é hook antes de ambiente**: um gate que estourou com `Traceback` costuma
imprimir `timed out` na linha seguinte, e hook quebrado disfarçado de contenção nunca viraria
alerta. **O default é a classe conservadora** — tratar o desconhecido como ambiente faria defeito
real virar laço infinito. **`--no-verify` continua proibido em qualquer classe**: a saída para
hook com bug é consertar o hook.

**4-quater. Os DOIS regimes, e o wrapper tem de funcionar nos dois.** Em **systemd** os hooks do
CLI do Claude Code **não existem** — são da sessão, não do sistema —, e por isso a allowlist do
wrapper é ali a **única** defesa. Provado sob `systemd-run`: as recusas saem com `status=2` e o
código nomeado, **pelo próprio código**. Na **sessão** os hooks se aplicam: eles bloquearam
**cinco** comandos meus nesta sessão, inclusive um patch cujo texto apenas *continha* os literais
de indexar e commitar. A saída correta é usar a ferramenta de edição ou montar os literais por
variável — **nunca** detectar o hook e pular, que é `--no-verify` com outro nome.

**4-quinquies. Três furos da porta, achados pela revisão adversarial e fechados com medição
(2026-09-16).** Nenhum deles aparecia em teste: os três exigiam medir o git, e não lê-lo.

1. **O `D` do vizinho entra pelo pathspec.** Medido num repositório de rascunho: com uma
   remoção **já estagiada por outra sessão** para um caminho que está **dentro** do pathspec
   pedido, `commit -F msg -- <caminhos>` leva essa remoção junto — o candidato se monta de HEAD
   **mais** o que estiver estagiado dentro do pathspec. Fora do pathspec, não entra. Como o
   índice deste repositório é **compartilhado**, a conferência de remoção só depois do `add`
   ficava vazia na volta seguinte. Agora ela roda **antes e depois**, e a recusa diz qual dos
   dois momentos reprovou. `tools/cerebro-commitar` não tem `reset`: quando o `D` já está lá, a
   porta **não estagia nada** e devolve a decisão ao humano.
2. **Leitura que escrevia o índice.** Medido em git 2.39.5, carimbando `.git/index`:
   `git status --porcelain` escreve o índice, e com `GIT_OPTIONAL_LOCKS=0` **não** escreve;
   `git diff --quiet -- <caminhos>` escreve **com ou sem** a variável — para o diff do worktree
   o refresh não é opcional. A porta usava exatamente esse `diff`. Trocada por **uma** leitura
   `status` sob `GIT_OPTIONAL_LOCKS=0`: mesma classificação (só-mtime sai vazio, conteúdo sai
   ` M`, novo sai `??`, estagiado sai `M `), mesmo custo medido (0,02 s contra 0,02 s) e **zero**
   escrita no índice que outra sessão pode estar usando.
3. **Duas réguas para a mesma família de rotação.** A família `<prefixo>-NN.jsonl` está escrita
   em **quatro funções e oito literais**: `alvos_do_registro` (`tools/run-daily-content`, glob
   `-[0-9][0-9].jsonl`, 2 literais), `shards_do_canal` e `portfolios_aguardando_commit`
   (`tools/publicar-estoque`, 2 cada) e `allowlist` (`tools/cerebro-commitar`, 2). As seis do
   Python usavam `\d\d`, que casa **dígito Unicode** — medido, `noticia-٠١.jsonl` (indo-arábico,
   `int("٠١") == 1`) entrava na allowlist da porta e **nunca** no glob do bash. Porta que aceita
   caminho que a cadeia jamais escreve é superfície a mais. As seis passaram a `[0-9]{2}`, e a
   paridade virou caso executável nos três instrumentos, inclusive para o ordinal **declarado no
   registro**: registro que o bash não saberia globar é ILEGÍVEL (exit 2 nomeando o campo), nunca
   família vazia em silêncio. **A dívida que fica**: quatro implementações da mesma regra
   continuam existindo. A rota de unificação é dar a `tools/listar-produtores-de-pagina` — já a
   fonte única do registro para os três consumidores — um modo `--arquivos shard|portfolio` que
   imprima `canal \t caminho` da família existente, e trocar os quatro pontos por ele; muda junto
   `tools/test_alvos_do_registro.sh`, cuja dublê de registro teria de emular o modo novo.
4. **Portfólio ESTAGIADO e não commitado era invisível ao bloqueio.** `portfolios_aguardando_commit`
   media com `git diff --quiet` (worktree contra índice) mais `ls-files --others`. Depois que outra
   sessão estagia, worktree e índice são iguais e o arquivo some dos dois — justamente o estado
   "aguardando commit" que a função existe para ver. A passada seguia e só o 6/9, que lê o
   diretório inteiro, reprovava, em **retomada**. Medido nesta data: `stj-acordao-derivado-02..08`
   estavam `A` no índice, estagiados por outra frente. Uma leitura `status --porcelain` enxerga os
   três estados e não escreve o índice.

E o que a bancada aprendeu sobre si mesma: o caso de symlink criava o link dentro de
`data/editorial/v2_pages/` **de produção** e o apagava com `rm -f`. Bancada não escreve em
produção — nem para provar que a porta recusa. O caso vive no cenário próprio, com `--raiz`.

**4-sexies. A PRIMEIRA EXECUÇÃO REAL, e o que ela mediu (2026-09-16, 17:45 e 17:52).** As duas
passadas terminaram em exit 1 e acordaram o dono. A leitura inicial foi "alarme falso"; a medição
diz o contrário, e três defeitos distintos apareceram juntos.

1. **O alerta estava CERTO.** A cadeia **parou na etapa 4/9**: `check derived-body-repetition`
   acusou **1.425 ocorrências**, todas em `stj-acordao-derivado-03.jsonl` — conteúdo de **outra
   frente**. `registra "texto-repetido"` é seguido de `exit 1`, então nada foi commitado nem
   publicado. Com o acervo bloqueado, exit 1 é o código correto e o `OnFailure` deve tocar.
2. **O rótulo mentia, e foi ele que induziu a leitura errada.** O driver imprimia
   `cadeia completou: sim` para uma cadeia parada em 4/9, porque lia `escopo` do
   `daily_content_runs.jsonl` — e o trap `EXIT` gravava `completa` sempre que `ESCOPO_DA_PASSADA`
   estivesse vazio, o que é exatamente o caso de um `exit 1` direto de gate. **Campo-proxy não é
   campo-fato.** A cadeia passou a gravar `escopo: parou_em_etapa` com `parou_em: "<etapa>"`, e
   um campo novo, `gerou`, que diz se o gerador do canal concluiu a 2/9.
3. **O critério de cobrança de tentativa não é "a cadeia chegou ao fim", é `gerou`.** Nas duas
   passadas a 2/9 concluiu (`noticias ok gravado: … (63 páginas)`) antes do gate parar tudo: as
   peças **foram** tentadas pelo produtor delas. Cobrar por "chegou ao fim" congelaria a contagem
   enquanto o gate global durasse — o laço silencioso — e cobrar em toda parada puniria a peça
   cujo gerador nem rodou.
4. **Duas causas viviam sob um rótulo só, e três peças foram PARADAS por causa alheia.** Medido
   sobre os 21 comentários aprovados do dia: **13 entraram**; dos 8 restantes, **4 têm página no
   estoque citando a notícia** (defeito real de enriquecimento, acionável) e **4 não têm página
   nenhuma** — o gerador monta página por (órgão × dia) e recusa grupo com menos de 4 itens (o
   log diz *"grupos abaixo de 4 itens: 81"*), então **nenhuma retentativa cria a página**. As três
   peças que chegaram a PARADO às 18:02 eram desta segunda classe. Ela agora é `sem_pagina`:
   reportada com a causa, com destinatário próprio, e **sem cobrar tentativa**. O discriminador é
   o artefato — o link da notícia aparece ou não no estoque —, nunca uma cópia da regra
   `not-<órgão>-<AAAAMMDD>` do gerador.
5. **Desfecho parcial previsto ganhou código próprio: exit 3.** Régua, na ordem: peça no teto →
   **1**; cadeia que parou em etapa → **1**; exit ≥ 2 da cadeia sobrevive; peça em quarentena
   abaixo do teto → **3**; nada pendente → **0**. A unit declara `SuccessExitStatus=3` e **só** o
   3 — exit 1 continua sendo falha de verdade, e uma lista que incluísse o 1 é reprovada pela
   bancada. É o mesmo desenho de `wikijuridica-djen-coleta.service`. A régua vive em
   `veredito()`, função pura, para poder ser medida por chamada direta.

**Dívida residual, nomeada:** as três peças carregam 3 tentativas cobradas sob a classificação
antiga. Se algum dia a página do dia delas existir, elas aparecerão como PARADAS e abrirão alerta
— destino correto (pauta humana), mas herdado de uma cobrança que hoje não se faria. Nada foi
apagado: o texto está em `data/ai/noticias_redigidas.jsonl` e o histórico em
`data/ops/publicacao_do_cerebro.jsonl`.

**8. O que ainda bloqueia a drenagem de acórdãos, com o número.** O timer
`wikijuridica-cerebro-publicar-acordaos.timer` nasce **instalado e adiado** em
`ops/systemd/timers-adiados.jsonl` (vence em 2026-10-16), pelo P6b-teto: com o oráculo do ingest
sobre as 30 páginas reais, `duplicate_phrase_with_page` acusou **29**, e **435 de 435 pares
(100%)** compartilham ao menos uma janela de 12 palavras — é **N−1 para qualquer N** e não
melhora com escala. A correção da moldura de `cmd/generate-acordao-pages` está em curso em outra
frente; fechada ela, remove-se a linha e `enable --now`.

## P7 — Destravar o DataJud

**Ordem recorrente do dono**, reafirmada em 2026-09-15: *"Sempre falo para destravar o
DataJud. Os dados no Brasil são públicos, o sigilo é exceção, e as páginas são informativas.
Não tem ilícito, não tem crime. Não crie uma lei que o próprio Brasil não criou."*

**Os dois motivos da trava caem, e o segundo era erro meu nesta sessão:**

1. *"Termo de uso do CNJ restringe uso comercial"* — é a cautela inventada que o §2 proíbe. O
   próprio §2 registra o precedente: a cláusula 3.8 foi citada neste repositório com uma
   ressalva de "autorização prévia por escrito" que **ela não contém**.
2. *"Lag de 42 dias torna o dado imprestável"* — **mantive a trava por isso e estava
   errado.** 42 dias inviabilizam **cálculo de prazo processual**; as páginas são
   **informativas** e não calculam prazo de ninguém. Defasagem conhecida se **declara** na
   proveniência.

**A prova de que o risco nunca foi real: o projeto JÁ faz isso, em produção.**
`cmd/social/processotela.go` serve consulta de processo individual do DataJud em superfície
pública — metadados e andamentos — com três desfechos escritos: encontrado; **`nivelSigilo >
0` ⇒ recusa sem nenhum campo** (*"segredo de justiça é a exceção taxativa do CPC, art.
189"*); e zero resultado ⇒ *"não localizado na base pública"*, nunca "processo inexistente".
A data do dado vai **no resultado**, não em rodapé. E a guarda real já existe em
`internal/datajudfila/detalhe.go`.

**A trava estrutural não protege nada que essa guarda não proteja** — ela só barra a rota
principal enquanto outra rota do mesmo projeto já entrega o mesmo dado. É incoerência, não
cautela.

**Escopo do que entra:** processo individual, número, classe, órgão julgador, relator,
andamento e **nome das partes**. CPC art. 189 é literal — *"os atos processuais são
públicos"* — e o segredo é lista taxativa. É o que JusBrasil e Escavador fazem há mais de uma
década.

**Fora fica só o que a lei nomeia:** `nivelSigilo > 0`, ECA, Maria da Penha, adoção, dado
sensível do art. 5º, II da LGPD. E identificador: CPF, RG.

### Execução: são DOIS enforcers, não um — e `internal/datajud` não existe

**Correção a uma afirmação minha.** Eu havia escrito que a trava era o teste. Verificado no
código: há **dois pontos de aplicação**, e reescrever só um deixa o outro barrando na primeira
compilação.

| # | onde | o que faz |
|---|---|---|
| 1 | `internal/codex2policyenforcement/policy.go:847` | **enforcer de runtime**: emite `codex2_policy_datajud_import_scope_escape` quando um arquivo importa `portaljuridico/internal/datajud*` e `datajudImportAllowed` (`:4492-4515`) devolve `false` |
| 2 | `internal/codex2policyenforcement/datajud_trava_estrutural_test.go:17-32` | **teste** que fixa a lista `caminhoDePublicacao` de 12 pacotes proibidos de importar |

**Os pacotes reais, medidos — `internal/datajud` NÃO EXISTE.** O prefixo do enforcer casa:
`internal/datajudfila`, `internal/datajudtpubatch`, `internal/codex2datajudobservations`,
`internal/codex2datajudfrontiersignalreport`. **Um plano que nomeasse `internal/datajud`
morreria na compilação.**

`datajudImportAllowed` (`:4506-4515`) permite o import quando o arquivo **importador** está
sob `internal/datajud*`, `internal/codex2datajud*` ou `cmd/*datajud*` — isto é, o dado pode
circular entre os pacotes de coleta, e o que está barrado é **exatamente a rota de
publicação**. É a trava a desfazer.

**Como se desfaz — pelos dois pontos, na mesma mudança, nunca por contorno:**

1. `datajudImportAllowed` deixa de decidir por **caminho do importador** e passa a decidir
   pelo que de fato protege: o import é livre, e o que o enforcer cobra é que a **fronteira de
   saída** filtre `nivelSigilo > 0` e carregue proveniência (URL, data, hash) e a nota de
   defasagem. A guarda de conteúdo já existe em `internal/datajudfila/detalhe.go`.
2. O teste passa a cobrar **essa** invariante, com prova por mutação: remover o filtro de
   `nivelSigilo` na fronteira ⇒ teste vermelho. Hoje ele cobra uma lista de imports, que é
   proxy, não proteção.

**O código de violação `codex2_policy_datajud_import_scope_escape` não some — muda de
sentido**: deixa de marcar "importou" e passa a marcar "serviu sem filtro de sigilo ou sem
proveniência".

**O agregado vira fila de pauta:** ordenar criação de página por volume real de litígio
(§1.16), maior lacuna primeiro.

## P5 — Fechar a lacuna de atribuição

**É a contrapartida do P4, e agora tem número.** Enquanto o molde afrouxa por medição, a
atribuição **aperta** — são as duas metades da mesma separação FATO × JUÍZO.

**Correção de enquadramento, e ela muda o regime desta frente.** Eu havia escrito que
atribuição imprecisa era *"P1 permanente, a única classe com risco real sob a OAB"*, e
transformado isso em pré-requisito bloqueante da escala. **Era invenção minha:** o Provimento
205/2021 e o **CED arts. 39 a 47-A** disciplinam **publicidade e captação**, não precisão de
citação em conteúdo informativo. Nenhuma norma disciplinar trata disso.

**E o texto oficial diz mais do que eu supunha — ele sustenta a posição do dono.** Conferido
no PDF oficial da OAB (Resolução 02/2015), o capítulo abre assim:

> **Art. 39.** A publicidade profissional do advogado tem **caráter meramente informativo** e
> deve primar pela discrição e sobriedade, não podendo configurar **captação de clientela** ou
> **mercantilização da profissão**.

A norma **exige** que a publicidade seja informativa; o que ela veda é **captação** e
**mercantilização**. Conteúdo informativo não é o risco — é o padrão que a própria norma
impõe. *(Eu havia citado "arts. 42-47", intervalo errado que omitia justamente o art. 39.)*

**O que fica de pé:** o defeito é real, é grande e conserta-se — conteúdo com artigo mal
atribuído é ruim para quem lê, e a plataforma vive de ser confiável para leitor humano e para
agente de IA. **O que cai:** o regime de bloqueio. **Esta frente roda em paralelo à
publicação, não à frente dela.** Atribuição frouxa rebaixa para **refino**, nunca impede a
página de existir.

> ### DEPENDÊNCIA DURA: "refino" só é destino se alguém drenar a fila
>
> Rebaixar para refino é a decisão certa **e cria uma obrigação**. §1.12, medido: a fila
> **tem produtor e não tem quem reescreva**. `v2_rewrite_queue.jsonl` é regenerada a cada
> ingest e **3.101 das suas 3.201 entradas são páginas VIVAS com defeito nomeado**; os únicos
> leitores são o classificador de severidade e dois gates de sitemap. **Dos 55 timers
> `wikijuridica-*`, nenhum é de refino.** Os reescritores morreram: `applied_rewrites` em
> **27/06**, `shard_rewrite_plan` em **05/09**.
>
> **A metade boa já funciona: "publica" acontece** — os 10.337 médios estão no ar, zero
> esperando. **A metade que falta é "refina depois"**, e sem ela mandar páginas para refino é
> *"publica e esquece"*.
>
> **Portanto: o P5 não fecha sem um consumidor de fila vivo e medido.** Construir esse
> consumidor é item do P8 e **já tem 3.101 páginas de trabalho esperando** — não é
> infraestrutura especulativa, é dívida acumulada. **A prova de aceitação do P5 inclui uma
> página entrando na fila e saindo dela refinada** — não basta o rebaixamento acontecer.

**O que a medição de §1.4 obriga a consertar, em ordem de gravidade:**

| defeito medido | volume | onde |
|---|---|---|
| artigo ausente do próprio `texto_citado` | **1.709 / 11.022 = 15,51%** | `extracao.go` — sem conferência de artigo |
| norma só atestada fora do trecho | **2.152 = 19,0%** | `triagem.go:195-230` testa no texto inteiro (`:200`, `:219`, `:225`) |
| nem artigo nem norma no trecho | **1.476 = 13,1%** | soma dos dois |
| páginas destravadas com atribuição não provada | **173 de 762** | cruzamento §1.3 × §1.4 |
| URN promovida sem `!art` conta como substantiva | **267 URNs, 79 acórdãos** | `main.go:380-387` não casa URN nua |

**Ofensores nomeados:** CPC/2015 **770**, Código Civil **186**, Código de Processo Civil
**147**. Caso concreto para o teste de regressão: acórdão `000812565`, `art. 1.021, § 4º` do
CPC atribuído a trecho que fala da **Súmula 282**.

1. **Atestar o `artigo`**: exigir que o número do artigo da URN ocorra dentro do próprio
   `texto_citado`, não em qualquer ponto do texto. Descarte **contado** em campo próprio.
2. **Catálogo de súmulas** de fonte oficial (STJ e STF publicam), com URL, data e hash, no
   molde de `internal/lexml/norm_registry_generated.go` + `data/source-audit/`. Súmula fora
   do catálogo não promove.
3. **Estreitar `NormaAtestadaNoTexto`** (`triagem.go:224`) para procurar dentro do
   `texto_citado`.
4. Cada mudança com **teste provado por mutação** e **constante de `revisao` nova**
   (`revisao_v9`) — é o mecanismo que reabre o que revisões anteriores fecharam
   (`extracao.go:175-180`).
5. **Medir antes e depois sobre a população inteira**, nunca sobre amostra enriquecida.
6. **Gabarito de atribuição**: 100 dispositivos sorteados, conferidos contra o texto oficial
   do artigo, congelados com data e método. É a régua com que o modelo novo da GPU será
   medido — e **régua feita depois do resultado não é régua**. Produzido pelo cérebro contra
   fonte oficial, com amostra de controle dos dois lados.

**Se isso derrubar a taxa de promoção, o número cai e está certo** — citação mal atribuída
custa mais que página a menos.

## P8 — Nenhum conteúdo parado

| Conteúdo | Volume | Destino |
|---|---|---|
| acórdãos candidatos sem página | **4.763** (medido, `-seco`) | páginas `stj-acordao-derivado`, pelo P6 |
| **agravos e embargos com ementa ≥ 250 palavras** | **17.616** | **ver abaixo — é o maior bolsão parado do repositório** |
| `propostas_reescrita.jsonl` | 100, zero aplicadas | regerar e aplicar — ver abaixo |
| `risco_superacao.jsonl` | 4.986 com par, 3.481 com risco | fila editorial — ver ressalva |
| acórdãos intocados pelo filtro | **17.691** | passada de parser, custo zero (§1.11) |
| grafo | 393.081 arestas | **não** vira rota nova — ver abaixo |
| `openai_review_batch_*` | 37 MB, resultado vazio | aposentar |
| `grafo_manifest.json` | sem leitor | religar ou aposentar com motivo |

### Os 49.807 agravos e embargos: 35,4% deles têm decisão fundamentada

Medição própria sobre os 60.221 registros do corpus (contagem de palavras **aproximada** —
regex `[^\W_]+`, não o `ptbrtext.BodyWords` do Go; serve para dimensionar a pauta, não para
decidir elegibilidade):

| faixa da ementa | barrados |
|---|---|
| 0–99 palavras | 6.213 |
| 100–249 | 25.978 |
| **250–399** | **11.251** |
| **400+** | **6.365** |
| **≥ 250 (soma)** | **17.616 = 35,4% dos barrados** |

**Top classes barradas:** `AGINT NO ARESP` 20.156 · **`ARESP` 11.553** · `AGINT NO RESP`
6.904 · `AGINT NOS EDCL NO…` 3.628 · `EDCL NO AGINT NO A…` 1.960.

> ### E TODO O CRIMINAL ESTÁ ATRÁS DO RADICAL `AGRG` — separar `AREsp` de `AgInt` não o alcança
>
> **Achado do agente de volumes, e ele muda o escopo desta frente.** O habeas corpus chega ao
> STJ como **`AgRg no HC`** — **51,5% da Quinta Turma** —, e `AGRG` é um dos oito radicais de
> `procedimental` (`main.go:316-324`). Consequência medida: **a Quinta Turma traz 33% dos
> acórdãos novos e apenas 6% dos candidatos**, e a taxa de candidato varia **38× entre órgãos**
> por causa disso.
>
> **Portanto a triagem por conteúdo desta frente cobre TRÊS veículos, não um:**
>
> | radical | o que carrega | por que não é procedimento |
> |---|---|---|
> | **`ARESP`** puro (11.553) | agravo em recurso especial | provido, o STJ **converte e julga o próprio REsp** |
> | **`AGRG` no `HC`** | **toda a matéria criminal** | o agravo regimental em HC decide **liberdade**, e o colegiado enfrenta o mérito da coação |
> | `AGINT` / `EDCL` | agravo interno e embargo | quando há mérito, está na ementa — e é o que a triagem lê |
>
> **Sem isto, a recuperação da coleta do P1 traz as turmas criminais (Quinta, Sexta e Terceira
> Seção, hoje NUNCA coletadas) e o filtro as barra na entrada por rótulo** — coletaríamos 64 mil
> acórdãos criminais para descartá-los sem olhar o texto. É exatamente o defeito que esta frente
> existe para corrigir, aplicado ao maior volume do corpus novo.
>
> A regra de parada de 16% continua valendo, **medida por veículo separadamente**: agravo em HC
> tem taxa de mérito estruturalmente diferente de agravo interno em AREsp, e uma taxa única
> esconderia as duas.

**Por que isso é conteúdo e não ruído.** O filtro `procedimental` (`main.go:311-324`) casa
por `strings.Contains` em 8 radicais e barra a classe **sem olhar o conteúdo**. Mas:

- **`ARESP` puro (11.553) é agravo em recurso especial** — quando provido, o STJ **converte e
  julga o próprio recurso especial**, decidindo o mérito. A sigla não diz se houve mérito; a
  ementa diz.
- **17.616 ementas com 250+ palavras** não são despacho de admissibilidade. Nessa extensão há
  fundamentação, dispositivo citado e tese.
- O dono é literal: **"conteúdo jurídico entra na plataforma"**, **"você não pode descartar"**.
  Agravo interno e embargo de declaração são decisões judiciais reais.

**A rota, e ela é exatamente a arquitetura do P4.** `procedimental` é hoje um gate de
**classe** — um rótulo — usado como se fosse juízo sobre conteúdo. Pela separação FATO ×
JUÍZO, a sigla é FATO (está no registro) mas *"esta decisão tem mérito autônomo"* é JUÍZO, e
juízo se decide pelo conteúdo, com evidência gravada:

1. **Triagem determinística primeiro, sem LLM:** ementa ≥ piso **e** dispositivo substantivo
   ancorado **e** ausência das marcas de não-conhecimento (Súmulas 7, 83, 182, 211, 284, 280,
   282, 356 e as fórmulas de admissibilidade que `sumulasProcessuais` e
   `dispositivosDeAdmissibilidade` já catalogam em `main.go:330` e `:362-375`). **A lista já
   existe — hoje ela só não é aplicada aos barrados por classe.**
2. **O cérebro julga a zona cinzenta**, não o lote inteiro: só o que passa na triagem e não é
   decidido por regra. Custo controlado por construção.
3. **Onde não houver mérito autônomo, o conteúdo ainda não se perde:** vira **página agregada
   por tese, por dispositivo ou por relator** — o mesmo material alimenta o grafo, os
   Percursos por fundamento legal e o inventário de fontes.

### MEDIDO — e o meu 17.616 era limite superior, não conteúdo aproveitável

A triagem determinística foi aplicada aos 17.616, com o catálogo que já existe no código:

| medida | valor |
|---|---|
| acusados de óbice pelas listas (`sumulasProcessuais` + `dispositivosDeAdmissibilidade`) | **14.757 (83,8%)** |
| união com detector de prosa de admissibilidade | **15.746 (89,4%)** |
| sem sinal de óbice | 1.870 |
| destes, com âncora substantiva | **1.388** |

**Ressalva que reduz ainda mais, e ela é minha obrigação registrar:** amostra por *stride* de
8 dos 1.388 mostrou que **5 de 8 ainda carregam óbice** que o detector não pegou —
`"SÚMULAS Nºs 5 E 7/STJ"`, `"PREQUESTIONAMENTO. IMPRESCINDIBILIDADE"`, `"FALTA DE
PROCURAÇÃO"`. **O resíduo real de mérito é de poucas centenas, não 1.388.** E em agravo
interno, *"negar provimento"* significa **manter** o não-conhecimento — não é sinal de mérito.

**A confirmação do defeito, porém, fica de pé:** `elegivel:515-517` retorna em `procedimental`
**na primeira linha**, e as listas só rodam em `:538-539` e dentro de `montaPagina`. **Não há
nenhum outro ponto de chamada.** O catálogo de triagem por conteúdo existe no código e
**nunca é aplicado** ao maior bolsão barrado — o descarte é por **rótulo de classe**, sem
olhar o texto. Corrigir isso é barato e o ganho, ainda que de centenas e não de milhares, é
conteúdo jurídico real que hoje some sem exame.

**Regra de parada, escrita antes do número:** se a triagem aprovar acima de **16%** dos 17.616
(o complemento dos 83,8% medidos), ela está mais frouxa que o catálogo atual e volta para
calibração. Decisão de não-conhecimento é maioria estatística em agravo — taxa alta denuncia o
detector, não o corpus.

*Nota lateral que confirma §1.1:* entre os barrados com ementa longa só aparecem **Quarta
Turma (9.317), Terceira Turma (7.898), Primeira Turma (317) e Segunda Seção (84)** — os
quatro únicos datasets que a coleta chegou a tocar. Corte Especial, Seções e as turmas
criminais não aparecem porque **nunca foram coletadas**.

**As 100 propostas não se descartam** (§1.15). O defeito é de engenharia: o gerador **não é
agendado** e **não termina** sobre o corpus atual — ele indexa candidatos por **norma
inteira**, e o CPC sozinho puxa ~28.595 acórdãos, tornando o laço TF-IDF inviável (~10⁸
cossenos). Correção: exigir **dispositivo em comum**, não podar por área. Volume tratável
medido por SQL: **4.302 páginas elegíveis, 425.755 pares**.

**Ressalva medida: o score de risco satura.** Das 4.986 linhas, **1.190 valem exatamente
1,0** — a fórmula `min(1, peso/5) × recência` satura com peso ≥ 5 e acórdão de menos de um
ano. Ordenar por ela é ordenar por nada. O sinal que não satura está no mesmo arquivo:
**`peso_apos_revisao`, de 0,20 a 142,00, mediana 1,20**. A fila ordena por ele, com laço por
**dispositivo** (mesmo artigo), não por norma.

**O que NÃO se publica desse dado:** o número do risco (nem em faixa), a palavra "superação"
e flexões, qualquer afirmação de que a tese mudou, e qualquer prognóstico — o §12 já manda
*"índice de reforma", nunca "chance de êxito"*. O dado mede **coincidência de dispositivo +
posterioridade de data**; não lê a ementa e não sabe se o colegiado decidiu igual, diferente
ou nem entrou no mérito. O enquadramento publicável é **inventário de fontes**, com nota de
escopo.

**Grafo não vira rota nova:** já sai em dataset e em 3 ferramentas MCP; a pergunta humana que
ele responderia já é a seção "Percursos por fundamento legal"; e 393.081 arestas em HTML é
*malha de links*, que pela matriz do §6 exige **purga ampla manual obrigatória**. A extensão
que vale é acórdãos por URN **dentro** de Percursos, na gêmea Markdown.

## P9 — Independência e auto-recuperação

**Independência não é o cérebro escrevendo em `public/`** — é **nenhum humano no laço**, com
o cérebro sinalizando, o systemd agindo e o gate julgando. O padrão já existe e funciona: o
cérebro grava `embeddings/ativo.json` e `wikijuridica-server-reload.path` reinicia o servidor
sozinho.

### Guardas mudas (§1.8)

- **flock — LACUNA FECHADA, e a rota que preserva o isolamento funciona.**
  `BindReadOnlyPaths` **convive** com `PrivateTmp=true`; **`PrivateTmp=false` é
  desnecessário**. O motivo não é ordem de aplicação: é que o `/tmp` privado **nunca chega a
  cobrir o `/tmp` real durante a montagem**. Fonte primária, `src/core/namespace.c` do pacote
  exato (systemd 252.39-1~deb12u2): sem `RootDirectory=`, `setup_namespace` monta em
  `/run/systemd/unit-root` (`:2134-2151`), com o comentário *"Always create the mount
  namespace in a temporary directory… prevents any mounts from being potentially obscured by
  other mounts we already applied"*; `prefix_where_needed` (`:2408`) prefixa só o **destino**;
  `append_bind_mounts` (`:377-394`) deixa a **origem crua**; e o caso `BIND_MOUNT`
  (`:1441-1465`) resolve a origem com `chase_symlinks(source, NULL, …)` — *"bind mount source
  paths are always relative to the host root"*. O `mount_move_root` vem só no fim.

  **Três condições obrigatórias, e inverter a ordem vira laço de boot:**
  1. **O `open` muda primeiro**, no código: sem `O_CREATE` **e** com `O_RDONLY`. Sem
     `O_CREATE` porque criar é o defeito; `O_RDONLY` porque sob bind read-only o `O_RDWR`
     falha com `EROFS` — e `flock(2)` é explícito: *"a shared or exclusive lock can be placed
     on a file regardless of the mode in which the file was opened"*.
  2. **Um snippet `tmpfiles.d` cria o lock.** `/usr/lib/tmpfiles.d/tmp.conf` tem
     `D /tmp 1777 root root -`: **`/tmp` é esvaziado no boot**. Origem ausente sem o prefixo
     `-` aborta o namespace com **226/NAMESPACE** — que é exatamente o laço de boot mudo da
     guarda (b). A ordenação já vem do `After=systemd-tmpfiles-setup.service` **implícito do
     `PrivateTmp=`**.
  3. **Só então** `BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock`, mantendo
     `PrivateTmp=true`. O `-` sozinho devolveria a mentira em silêncio; por isso ele vem
     **com** o snippet, nunca no lugar dele.

  **Corrigindo uma suposição minha:** tirar o `O_CREATE` **não basta**. Dentro do `/tmp`
  privado o resultado passa a ser `ENOENT` ⇒ "livre" ⇒ **o mesmo veredito errado, sempre**. O
  namespace tem de ser religado de qualquer forma.

  **Prova empírica a rodar na execução** (não cabe em plan mode), com `PrivateUsers=yes`
  porque é gerenciador de usuário:
  `systemd-run --user --wait -p PrivateUsers=yes -p PrivateTmp=true -p BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock /usr/bin/stat -c %i /tmp/opt-wiki-agent-heavy.lock`
  e comparar com o inode do host — hoje **39454263 (host) × 39739472 (daemon)**. Iguais =
  corrigido.

  Mais **gate estático**: unit com `PrivateTmp=true` + lock sob `/tmp/` sem `BindPaths`
  correspondente ⇒ vermelho.
- **limiter:** `[Unit] StartLimitIntervalSec=600` (em `[Service]` é ignorada **em
  silêncio**), `nrestarts_cerebro` em `check-portal-health`, e **gate estático**: unit com
  `Restart=always` precisa de `StartLimitIntervalSec > RestartSec × StartLimitBurst` **ou**
  detector nomeado.
- **watchdog:** `WatchdogSec=1200` + `NotifyAccess=main`, com `WATCHDOG=1` batido **de dentro
  do laço `Roda`**, nunca de goroutine com ticker cego — ticker continuaria batendo com o
  `Passo` travado. 1200 s cobre o `Passo` legítimo mais longo (~1.000 s). **Pausa não deve
  tropeçar no watchdog**: quem detecta pausa é o gate, não o watchdog.

### A pausa que nunca sai

`Roda` loga a pausa **uma única vez** e dorme para sempre; o processo fica `active
(running)` — verde para o systemd e produzindo zero. Pausa vira **objeto contado e
classificado**, com limiares diferentes por natureza: `ocupacao` (flock, loadavg) 30 min;
`portal` 15 min; `infra`/`ambiente` **25 min**, derivado de `OLLAMA_KEEP_ALIVE=15m` — modelo
que o próprio cérebro carregou evapora em 15 min, então pausa por teto de residentes que
dura mais que isso não é concorrência transitória.

"De propósito" é **declarado**, não inferido: `data/ops/cerebro_pausa_manual.json` com campo
`ate`. **Passado o prazo, a pausa manual vira defeito** — pausa declarada que ninguém retirou
é a forma mais comum de "esqueci desligado". **Nunca auto-limpar a pausa**: a recuperação é a
causa sumir, não a guarda ceder.

### Batimento e gate

Dois arquivos: `cerebro_batimento.json` (estado atual, reescrito a cada `Passo`, temp+rename,
nunca cresce) e `cerebro_batimento.jsonl` (append **só nas transições** — a 30 s de cadência,
um append por batimento daria 2.880 linhas/dia de ruído).

O campo que resolve o problema do dono é **`proximo_batimento_ate`, declarado pelo próprio
worker**: ao iniciar lote, `agora + prazoDoLote(n) + margem`; ocioso ou pausado,
`agora + IntervaloOcioso + margem`. Assim o gate **não precisa conhecer nenhuma flag do
daemon**.

| situação | `ts` | estado | pendente | veredito |
|---|---|---|---|---|
| GPU esvaziou a fila | fresco | ocioso | 0 | **VERDE** |
| worker morto ou travado | **vencido** | qualquer | qualquer | **VERMELHO** |
| pausado a pedido, no prazo | fresco | `pausado_a_pedido` | — | **VERDE** |
| pausado por defeito | fresco | `pausado_por_defeito` | — | **VERMELHO** com classe+sonda+duração |
| fila cheia, nada elegível | fresco | ocioso | >0, elegível 0 por >15 min | **VERMELHO** (relógio ou backoff travado) |
| arquivo ausente | — | — | — | **VERMELHO** (falha fechada) |

**Onde roda:** unit própria com `OnFailure=` e **sem** `SuccessExitStatus=`, timer de 15 min.
**Não** só na bancada diária, que é rodízio orçado e mascara exit 1 (§1.10).

### Retentativa que não é teimosia

- **Erros tipados** em `internal/ollama` (`ErrIndisponivel`, `ErrServidor`,
  `ErrModeloAusente`, `ErrRecusado`, `ErrRespostaIlegivel`), classificados em INFRA /
  AMBIENTE / CONTEÚDO.
- **`Fila.Devolver`**: volta a `pendente` **sem consumir tentativa** — `Reivindicar` já
  incrementa em `fila.go:409` apostando que a falha é do trabalho, e falha de infra refuta a
  aposta.
- **Disjuntor no WORKER, não na tarefa**: backoff por tarefa não resolve tempestade de 500 —
  o worker voltaria em 30 s e pegaria as 3 seguintes, queimando 34 mil em horas. Backoff
  global 30 s → 15 min, **zero chamada ao Ollama enquanto pausado**.
- **`done_reason=length` NÃO vira terminal — PARTE A ENTRADA.** *(Reversão de uma proposta
  minha: eu havia escrito "terminal na primeira vez, porque as três tentativas cortam no mesmo
  lugar". A medição refutou.)* O veredito é **(b) ementa densa demais para o teto**, não laço
  degenerado — §1.13 traz as quatro evidências, com a dose-resposta monótona por tamanho de
  entrada (0% abaixo de 1k chars, 5,56% acima de 5k) e a ausência total da assinatura de laço
  nas 5.930 concluídas. Matar a tarefa seria **descartar as ementas mais densas do corpus**,
  que são justamente as mais ricas em dispositivo (30 menções contra 5 da população).
  **Correção: partir por item numerado**, com **corte por parágrafo** para as **7 das 36** que
  não têm item numerado nenhum. Custo evitado: **~63 falhas ≈ 8 h** nos 34.796 pendentes.
- **Persistir o texto cortado continua valendo** (`extracao.go:475-476` o descarta), agora não
  para decidir entre (a) e (b) — já está decidido —, mas para escolher o ponto de corte e
  medir a margem do modelo sobre o parser, **que não foi medida**.
- **Lápide não é defeito**: estado `superada` separado de `erro`, senão o gate nasce com 5
  vermelhos permanentes — e vermelho permanente é vermelho que se aprende a ignorar.
- **Jitter** de ±20% no `disponivel_em`, senão as 3 tarefas do lote voltam no mesmo instante
  contra o mesmo Ollama quebrado.

### Auto-recuperação do ambiente (o caso do servidor novo)

- **Modelo ausente**: sonda nova `/api/tags` (não existe hoje em `cliente.go`) × modelos
  distintos das tarefas pendentes. Ausência **pausa com diagnóstico nomeado**, **nenhuma
  tarefa é tocada** — é o que torna impossível o cenário "34 mil linhas mortas". `--puxar-
  modelo-ausente` opcional, padrão desligado.
- **`size_vram` como ponteiro `*int64`**, não `int64`: campo ausente decodificaria como `0`,
  e `0` significaria "nada em VRAM" — a guarda voltaria a medir a coisa ao lado do perigo.
  `nil` = campo ausente ⇒ diagnóstico nomeado.
- **Fila corrompida**: `PRAGMA quick_check` em `Abrir`; corrompida ⇒ move para
  `.corrompida-<ts>`, recria, e o `.timer` reconstrói. **Sempre alerta** — recriar a fila é
  fato, nunca silêncio.
- **Relógio/lease**: `disponivel_em` comparado lexicograficamente; salto de NTP para trás
  empurra tarefas para um futuro que nunca chega ⇒ **fila cheia que parece vazia**. Batimento
  grava `pendente` **e** `elegivel_agora` separados.
- **Esquema v3**: colunas novas, **sem tocar no `CHECK(estado IN ...)`** — binário revertido
  passaria a falhar em toda escrita.

### O cérebro nunca ocioso

Com GPU a fila drena em ~28 h e ele dorme. **O mecanismo não é mexer em `Reivindicar`** (que
já é a escada: `ORDER BY prioridade DESC`), é **garantir estoque**: campo `Reabastecedor` no
`Worker`, chamado em `Roda` exatamente quando `err == nil && n == 0` — fila vazia **e**
portal são. Estrangulado (≥1 h ou mtime mudou), anda os degraus de cima para baixo e **para
no primeiro que produziu estoque**, com estoque medido em **horas de trabalho** (24 h), não
em varredura completa.

**Faixas de prioridade que não se sobrepõem** (hoje `medir_modelo` em −10 cai dentro da
faixa de extração, −5..−24): bandas de 100, com invariante testável
`min(D_n) > max(D_{n+1})` no pior caso.

**O degrau infinito** é reprocessar o acervo com o melhor par `(modelo, versão_do_prompt)`.
Ele converge e para entre mudanças — e **é isso que o impede de virar laço**. Reprocessa sse:
existe linha para a chave; o hash do texto ainda bate; o par da última linha **difere** do
vigente; o par vigente venceu **medição pareada gravada**; e a triagem diz `BaldeModelo`.

**Bloqueio descoberto:** a fila **não suporta** reprocessar por prompt novo — a impressão é
`ImpressaoDoTexto(ementa)`, função só do texto, então trocar o prompt com o mesmo modelo cai
em `INSERT OR IGNORE` e nunca executa. O próprio código admite em `extracao.go:135-136`. A
versão do prompt (já gravada em `:612`) tem de entrar na identidade e no cache.

**Poda:** não há `DELETE` em `fila.go`; a fila está em 134 MB para ~54 mil linhas (~2,5
KB/linha, a ementa viaja no payload), e um ciclo de reprocessamento acrescenta ~100 MB.
`Podar` apaga **só** `concluida`, e só de tipo com artefato append-only correspondente — a
fila é declaradamente estado regenerável.

**A linha do anti-desperdício:** *uma chamada ao modelo é trabalho válido quando pode mudar
um bit de um artefato que alguém lê; é moer água quando o resultado é previsivelmente
idêntico ao já gravado.* **Nenhum teto de tokens, de lote ou de fila** — os tetos que ficam
têm causa externa (CED art. 42, earlyoom, anti-travamento), nunca econômica.

## P4 — Arquitetura nova de gates: FATO × DIVERGÊNCIA × PUBLICIDADE × JUÍZO

> **Cabeçalho corrigido.** A versão anterior dizia *"e o cérebro julga o que é juízo"*. O
> workflow de arquitetura refutou isso com três evidências (§"O ângulo cérebro como juiz CAIU").
> **Quem julga estatístico é o CENSO**, que já classifica como MÉDIO — e MÉDIO publica.
> **DIVERGÊNCIA é bug** e se fecha por paridade de régua, não por modelo. O cérebro fica onde há
> **texto a ler** (atribuição de citação), não onde há limiar a comparar.

**Esta é a frente que o dono ordenou de forma mais direta, e a que destrava mais conteúdo.**
*"Precisa planejar uma nova arquitetura. Não quero ficar repetindo. Os gates têm muitos bugs e
travam a fábrica à toa, sem motivo."* · *"Ou deixar o gate mais inteligente ou desativar."* ·
*"Tem conteúdo que é bom e os gates acusam como ruim — ou, quando é ruim, tratam como bom. O
cérebro deve decidir pelo contexto."*

### Os cinco defeitos medidos que ela conserta (§1.17)

| # | defeito | prova |
|---|---|---|
| 1 | produtor e gate usam réguas diferentes | 3-grama com dígito neutralizado × 5-grama com dígito preservado, mesmo limiar 0,70 |
| 2 | neutralizar dígito apaga o identificador do acórdão | "REsp 1.794.991" ≡ "REsp 2.150.333" depois de `main.go:2189` |
| 3 | o detector mede a fonte e o template, não a nossa prosa | `corpoDaPagina` soma ementa oficial + camada autoral + FAQ fixo (`:1597-1628`) |
| 3b | **o regex de itens mede a quebra de linha do COLETOR, não a qualidade da ementa** | `(?m)^[ \t]*\d{1,2}\s*\.\s` exige marcador em **início de linha**, com **ponto** e **espaço**. Taxa de recusa por arquivo de coleta: `2025-11` **74,3%** · `2025-12` 32,8% · `2026-04` 0,6% · `2026-07` **0,0%** · `2026-08` **0,0%**. **A mesma ementa passa ou falha conforme o mês em que foi baixada.** Dos 682 recusados, **667 têm marcador em alguma posição e ZERO estão sem numeração**: meio de linha 368 (54,0%), ponto sem espaço 186 (27,3%), hífen 99 (14,5%), colado à pontuação 18 (2,6%). **25 de 25 amostradas são ementas legítimas e substantivas; 0 inaproveitáveis.** Exemplos lidos: REsp 1.984.639 (`1- Recurso especial…`, hífen), REsp 2.057.373 (`1.Não há violação…`, sem espaço), REsp 2.219.797 (item colado ao cabeçalho em versal). **344 dos 682 são a ementa estruturada NOVA do STJ** ("I. Caso em exame") e **570 vêm do que a IA local destravou** |
| 4 | o gerador ocupa o espaço da fonte e depois mata a página | camada autoral e FAQ montados antes da citação (`:1630-1670`); **144 páginas** |
| 5 | recusa por juízo é terminal e não deixa rastro | 532 + 123 + 84 + 21 somem por passada, sem linha auditável |

### O eixo da arquitetura

**FATO não se interpreta; JUÍZO não é terminal.**

| classe | exemplos | regime |
|---|---|---|
| **FATO** | campo ausente, encoding quebrado, corpo vazio, `intent` duplicado, coerência de artefato (HTML + sitemap + `published_manifest` + SHA-256), anti-fraude, sigilo | **terminal e inegociável** — são fatos verificáveis, não juízos |
| **DIVERGÊNCIA** | dois instrumentos afirmam medir a mesma coisa e não medem: régua do produtor × régua do gate; piso na entrada × piso na saída; regex que mede a quebra de linha do coletor | **é BUG, não juízo.** Não se resolve por limiar nem por modelo: resolve-se fazendo um **chamar o outro**. Contém 100% do excesso medido |
| **PUBLICIDADE** | promessa de resultado, preço como chamariz, captação indevida, CTA comercial, inscrição na OAB nas peças sociais | **terminal onde há publicidade** (Prov. 205/2021; CED arts. 39 a 47-A). **Não alcança página informativa** — o art. 39 exige que a publicidade seja *"meramente informativa"* |
| **JUÍZO** | similaridade, molde, densidade, thin content, pisos de contagem, regex de transcritibilidade, **atribuição de citação** | **nunca terminal**: régua alinhada ao gate real, camada certa, veredito do cérebro com evidência, e rebaixamento para fila de refino em vez de morte |

**A atribuição de citação mudou de coluna, e por quê.** Ela estava em FATO como *"P1
permanente sob a OAB"*. O enquadramento era falso: nenhuma norma disciplinar trata de
precisão de citação em conteúdo informativo. Ela é **defeito de qualidade medível** —
conserta-se no produtor (P5), mede-se antes e depois, e a página **publica e refina**. O que
a mantém séria não é sanção, é que a plataforma vive de ser confiável para leitor humano e
para agente de IA.

**Não é afrouxar gate — o contrato já abriu essa porta e ela está vazia.** O §5 diz:
*"Gate estatístico refutado por medição é pulado, com a evidência gravada — e refutar exige
medir, nunca opinar."* O mecanismo existe no papel e **nunca teve quem o exercesse em
escala**, porque medir caso a caso é trabalho humano. É o buraco que o cérebro preenche.

O repositório já pagou os dois erros: um detector acusou **46 páginas e as 46 eram falso
positivo**; e um gate passou **verde** com 14 de 17 testes quebrados.

### Decisão tomada: conteúdo curto NÃO é conteúdo ruim

**Ordem do dono, 2026-09-15:** *"Mesmo com poucas palavras, o conteúdo é legítimo. Travar
isso é loucura. É dinheiro desperdiçado."*

**Ele está certo, e o defeito é de grandeza, não de régua.** São dois números 250 diferentes,
com o mesmo valor, medindo coisas distintas:

| onde | o que mede | consequência |
|---|---|---|
| gate de publicação (`CLAUDE.md` §5) | **corpo da PÁGINA** — ementa citada + camada autoral + FAQ | correto: página fina não indexa |
| gerador (`elegivel`, piso de 250) | **ementa de ENTRADA**, sozinha | **errado: mata a matéria-prima antes de somar o que nós escrevemos** |

Uma ementa de 120 palavras com dispositivo ancorado gera página de 600 palavras depois da
camada autoral. **O gerador a descarta como se a página já estivesse pronta.** São **4.500
acórdãos** barrados por `ementa_curta_demais_para_duas_camadas`.

**Correção:** o piso sai da entrada e vai para a **saída**, onde o gate real já o aplica —
`montaPagina` já tem `corpo_abaixo_da_banda_do_verbete` (`:1679`) e
`comentario_proprio_abaixo_do_piso` (`:1682`), que medem a página montada. **A conferência
certa já existe a jusante; o piso a montante é redundante e destrutivo.** O que o gerador
deve exigir na entrada é o que de fato define aproveitabilidade: **dispositivo substantivo
ancorado** e **item transcritível**, não contagem bruta de palavras da fonte.

**MEDIDO, e o resultado é devastador para o piso atual:**

| medida sobre as 4.500 barradas | valor |
|---|---|
| mediana de palavras da ementa | **161** |
| p90 / máximo | 231 / 249 |
| **com ≥ 25 palavras** (o mínimo real de citação, `main.go:96`) | **4.496 de 4.500** |
| **com ≥ 42 palavras** (a menor camada citada entre as 2.488 páginas ACEITAS) | **4.476 de 4.500** |
| com menos de 25 palavras | **4** |

**O que a ementa precisa entregar não é a página: é a camada citada, cujo mínimo é 25 — dez
vezes menor que o piso aplicado.** A camada autoral vem dos **metadados**, não da ementa: na
passada exaustiva ela teve **mínimo de 355 palavras**. Ou seja, a página nasce acima do piso
mesmo com ementa curta, e o gerador a mata antes de montar.

**4.496 de 4.500 páginas são recusadas por um piso que mede a grandeza errada.** Apenas 4 são
genuinamente pequenas demais.

**A prova mais forte, e ela é negativa:** nos 4.763 candidatos processados, os cortes de saída
— `corpo_abaixo_da_banda_do_verbete` (`:1679`) e `comentario_proprio_abaixo_do_piso` (`:1682`)
— **dispararam ZERO vezes**. Nem aparecem na lista de recusas. **Os pisos que medem a grandeza
certa nunca mordem; o que morde é o que mede a grandeza errada.**

**Por que são incomparáveis, no código:** `main.go:2176` define `corpoAutoral` como o corpo
inteiro **menos o que está entre aspas curvas**. A camada autoral é feita de **metadado** —
órgão, relator, URNs, súmulas, precedentes, contagens do acervo, FAQ. **Da ementa vêm ~13
palavras.** O que a ementa precisa entregar de verdade são as **25** de `minimoCitacaoOficial`.

**Volume destravado, bruto e líquido separados:**

| medida | valor |
|---|---|
| dos ~4.500, com âncora substantiva | **805 ≤ x ≤ 2.477 — dois agentes divergem (§1.20f)** |
| destes, com citação ≥ 25 palavras pela regra de item **atual** | 1.930 *(sobre a contagem alta)* |
| com a regra de item **corrigida** | **2.426** *(idem)* |
| **líquido estimado**, depois do anti-molde (que recusou 36,1%) | **~1.500–1.600** *(sobre a contagem alta; sobre a baixa, ~500)* |

**A divergência está aberta e é medível em uma passada** (§1.20f): o agente de pisos mediu
2.477, o crítico de completude mediu 1.225 testando três definições de âncora e propôs 805 como
estrato honesto. A hipótese de desempate — um contou com a sobreposição do cérebro e o outro
sem — é sustentada pela aritmética (a diferença de 1.252 é da ordem das 2.203 promoções).
**Nenhum dos dois números entra como fato até a passada de desempate.**

O líquido é **estimativa** — o número exato sai do binário com a constante trocada. Todos os
2.477 têm peso de evidência **≥ o mínimo dos candidatos que o gerador já aceita**.

**Proveniência da constante, e ela fecha o caso:** o 250 nasceu num **único commit,
`45d33ee8`, de 2026-09-10 — cinco dias atrás, nunca revisado**. E o comentário em `:400`
entrega o critério real: *"com 250 palavras sobram 1.674 candidatos"*. **Foi calibrado para o
TAMANHO DO POOL, não para qualidade de conteúdo.**

**A regra de parada, escrita antes do número:** conteúdo curto entra se a página montada
passar o piso na saída; não entra se a página montada continuar fina — porque aí o defeito é
da página, não do piso.

### A ordem do P6 — travessia mínima, depois paridade, depois o lote

**Correção de uma versão anterior deste bloco.** Eu havia escrito *"publicar as 2.488 primeiro,
corrigir as réguas depois"*. **A síntese do modo-operação (17 agentes) e a L2 do red-team
derrubam isso**, e o motivo é de produção, não de gosto:

- **L2 é bloqueante:** `lane` e `pageType` têm de estar certos **antes da primeira gravação**.
  Corrigir depois é mudança de **atributo servido sem mudança de texto** ⇒ `--ressemear` sobre
  2.488 rotas, re-datando o acervo e re-anunciando tudo ao Googlebot.
- **A contenção também manda:** o lote grande depois da paridade evita gerar 2.488 páginas com a
  régua que o §1.17 já provou dominada, para reprocessá-las em seguida.

**A ordem, então, é esta — e ela está no prompt de execução:**

| # | passo | por quê |
|---|---|---|
| **1** | **travessia mínima**, com os gates atuais e `lane`/`pageType` **já corrigidos** | o menor lote que exercita **todos** os elos de uma família inédita: preservação, pareamento contra o commit pai, pre-commit, censo, transação, smoke |
| **2** | **P4 — paridade de régua** (cinco eixos), piso na saída, regex em fallback | é o conserto da DIVERGÊNCIA; 135 de 135 recusas caem |
| **3** | **`-seco` de recenseio** | mede o poço **com a régua certa**, e é o número que decide o lote |
| **4** | **lote** | `-limite` aberto, sem cadência de calendário |

**O que a travessia preserva:** um defeito que apareça nela é atribuível **a ela**, não à mistura
de "gate novo + família nova". O que ela **não** faz é publicar o poço — isso é o passo 4.

### As três correções já medidas e prontas para executar

Não dependem do workflow: cada uma tem a régua substituta e o teste de regressão já rodados.

**1. Régua de molde — alinhar ao gate que decide publicação.** Cinco eixos (§1.17). A prova de
que não é afrouxamento: a régua real **aprova 135 dos 135** pares que a do gerador recusa, e
reprova **0** que ela aceita — é estritamente dominada. E o máximo da família sob a régua real
é **0,5193**, contra limiar 0,70. **Destrava até 1.405 páginas.**
*Ordem de aplicação, pelo efeito isolado medido:* remover a neutralização de dígito zera as
135 sozinha; stopword-drop deixa 1; 5-gramas deixa 6; excluir headings deixa 14. **Aplicar os
quatro**, porque o objetivo é *a mesma régua*, não *uma régua melhor*.

**2. Piso de palavras — sai da entrada, fica na saída.** Os cortes de saída dispararam **zero
vezes** em 4.763 candidatos; o piso de entrada matou 4.500. **Líquido estimado: ~1.500–1.600
páginas.** A constante é de `45d33ee8` (2026-09-10) e foi calibrada para tamanho de pool, não
para qualidade.
*Forma exata da correção:* trocar `pisoEmentaPalavras` por um **piso de corrida transcritível
de 25 palavras** — que é o que o gate a jusante realmente exige (`minimoCitacaoOficial`,
`:1655`) — e deixar `:1679` e `:1682` decidirem, já que **nunca reprovaram ninguém**. Também
dispararam zero: `sem_duas_fontes_oficiais_verificaveis`, `title_fora_da_faixa_de_seo`,
`meta_description_fora_da_faixa` e `fragmento_terminal_em_campo_visivel`.
*Distribuição da ementa nos 4.500:* min 1 · p25 117 · **mediana 161** · p75 202 · máx 249.
*Honestidade sobre o líquido:* os curtos saem **pior** no anti-molde — citação mediana 135
contra 151, peso p25 de 3 contra 6 —, e é por isso que 2.477 brutos viram ~1.500–1.600.

**2b. `integralmenteEmCaixaAlta` trunca citação de página que JÁ PASSA** — mesma causa-raiz do
item 3, e atinge quem hoje funciona. Medido: no **REsp 2.172.296** a citação saiu com **42
palavras** porque a corrida parou no cabeçalho `"II. QUESTÃO EM DISCUSSÃO"` da ementa
estruturada nova do STJ. Não é recusa: é **página publicada com menos fonte do que devia
ter**.

**3. Regex de itens transcritíveis — aceitar as formas reais da fonte.** Regra substituta
medida: sequência consecutiva 1, 2, 3… com separador **ponto ou hífen**, **com ou sem
espaço**, e fronteira à direita que não seja dígito — esta última mata `art. 1.022` e
`R$ 15.000`, que é o falso positivo óbvio. **Recupera 675 dos 682.**
**E o teste de regressão foi rodado:** sozinha, ela **quebra 29 dos 4.079 que hoje funcionam
(0,71%)** — ementas que não começam em "1". **Portanto entra como FALLBACK** (ou escolhe-se a
maior das duas corridas): **675 recuperados, 0 regressões por construção**, e 107 dos 4.079
ganham citação maior. *(Este é o tipo de verificação que o contrato exige e que quase não foi
feita: a regra "melhor" isolada teria introduzido 29 defeitos novos.)*

### O desenho completo — FECHADO por workflow de 13 agentes

Cinco varreduras do mapa de gates, três arquiteturas por ângulos independentes, três refutações
adversariais, crítico de completude e síntese. **Nome: PARIDADE — o produtor mede o que o gate
mede, e toda recusa tem nome.** Registro durável em
`~/.claude/plans/pure-imagining-cerf-agent-a165e10e45052cc63.md`.

#### A terceira categoria que faltava: DIVERGÊNCIA

Eu havia desenhado duas classes (FATO e JUÍZO). **Faltava a que contém 100% do excesso medido:**

> **DIVERGÊNCIA é quando dois instrumentos afirmam medir a mesma coisa e não medem.** Não é
> fato nem juízo: **é bug.** Não se resolve escolhendo limiar, criando banda ou chamando modelo.
> Resolve-se fazendo **um chamar o outro** — e o número que sobrar depois disso é o número real,
> sobre o qual se decide.

| classe | o que é | quem decide | julgável por contexto? |
|---|---|---|---|
| **FATO** | proposição verificável sobre o artefato ou a fonte | código determinístico | **nunca** |
| **DIVERGÊNCIA** | dois instrumentos, mesma pergunta, respostas diferentes | medição A/B | **nunca — é defeito a fechar** |
| **JUÍZO** | heurística estatística sobre semelhança ou densidade | **o censo**, como MÉDIO | **sim, e MÉDIO publica** |

#### O achado que torna o §5 do contrato inexecutável hoje

**Toda recusa estatística do produtor é um `continue` e um `++` num `map[string]int`**
(`main.go:294-297`, relatório em `:2268-2312`). **Nenhum `intent_id` vai para o disco.** Logo
**nenhuma das 1.405 recusadas pode ser nomeada — muito menos refutada.**

O §5 do contrato manda: *"gate estatístico refutado por medição é pulado, **com a evidência
gravada**"*. **Sem ledger, a regra é literalmente impossível de cumprir.** É por isso que o
mecanismo nunca foi exercido: não faltava disposição, faltava o registro.

#### Medição nova: a composição do corpo sozinha já explica quase tudo

Sobre a população viva inteira, **só trocar o corpo comparado** (excluir headings e FAQ, que o
gate exclui de propósito em `AssembleBody:152-154`) leva a mesma régua de **13 para 134 pares**
acima de 0,70, e de 22 para **122 de 1.074 páginas** — **páginas que já estão no ar e que nenhum
gate vivo reprova**. Somado o tokenizador, os 134 vão a **0**. *(Este segundo trecho tem
ressalva de população declarada pelo próprio autor.)*

#### As quatro camadas, em ordem

```
C0  FATO ......... terminal, e agora COM NOME no ledger     (veredito inalterado)
C1  PARIDADE ..... o produtor chama a função que o gate usa  (É O CONSERTO)
C2  LEDGER ....... toda recusa gravada com intent_id         (torna refutável)
C3  CENSO ........ estatístico = MÉDIO = publica             (já é a política vigente)
C4  ESCOPO ....... procedimental, medido antes               (frente própria, §P8)
```

#### Duas fases, e a fronteira é uma medição — não uma opinião

- **Fase 1:** paridade + ledger. **A terminalidade do produtor fica INTACTA** — `main.go:294`
  continua recusando, só que com a régua certa e gravando o nome.
- **Fase 2, só se a medição da Fase 1 autorizar:** `molde_acima_do_limiar` deixa de ser terminal
  e vira MÉDIO.

**Honestidade que o autor fez questão de registrar, e eu mantenho:** *"enquanto a Fase 2 não
acontecer, este plano não põe uma página no ar"*. Quem publica as 2.488 é o P6, que não depende
disto — e é por isso que a ordem do roteiro separa os dois.

#### O caminho para o censo existe, e custa UMA linha

Página recusada por `continue` **nunca vira linha de shard**, então o censo não a vê. Para o
resíduo chegar lá: (a) a página é **montada e gravada** com o motivo no ledger; (b) o motivo
entra em `data/editorial/v2_rewrite_queue.jsonl`, que o censo **já lê** como `queue_reasons`
(`tools/generate-v2-publication-severity:768`), e ganha **uma linha** no bloco
`# --- medios (publicam) ---`: `medium.append("molde_refutado_por_medicao")`, ao lado de
`batch_global_similarity_refutado_por_medicao` (`:764-765`), que é o vizinho de mesmo eixo.
**Uma linha de Python, num bloco que já existe, e nunca em `critical`.**

#### O ângulo "cérebro como juiz" CAIU — e os três motivos são verificados

1. **A máscara não tinha constantes de onde derivar:** os headings e as molduras de FAQ são
   concatenação `+` inline (`main.go:1596-1630`, `:2011-2016`, `:2044-2048`), não `const`.
2. **O custo por tarefa varia 2,8× entre dias** no próprio ledger — a banda orçamentária que
   justificaria o juiz não tem fundamento.
3. **O detector em camadas que ele queria que um 4b julgasse já existe, em Go, determinístico, e
   roda.**

**Não há LLM em nenhum caminho de veredito desta arquitetura.** O cérebro continua onde rende:
extração, embeddings, fila de enriquecimento. *(Correção a mim mesmo: eu havia desenhado o
cérebro como julgador de gate no P10. O julgador é o **censo**, que já classifica estatístico
como MÉDIO em 10.337 páginas vivas. O cérebro entra onde há texto a ler, não onde há limiar a
comparar.)*

#### O que nenhuma linha desta arquitetura toca

Anti-fraude · coerência de artefato (os 9 códigos de `qualitygate.go:21-31` mais
`publishedmanifest.Validate` no boot) · ética de publicidade (`internal/oabgate.CheckResposta`,
que **só pode ficar mais estrita**) · **citação legal** (`validate.go:29-39`,
`maxLegalCitationSpanWords=40` + `isLegalCitationExempt`, com a guarda anti-hub do red-team de
2026-07-22 — **e este gate está VIVO**) · sigilo (`elegivel:526` →
`stjacordaos.MotivoBarrado`) · campo ausente, corpo vazio e encoding.

**Não é afrouxar gate — o contrato já abriu essa porta e ela está vazia.** O §5 diz:
**"Gate estatístico refutado por medição é pulado, com a evidência gravada — e refutar exige
medir, nunca opinar."** O mecanismo existe no papel e **nunca teve quem o exercesse em
escala**, porque medir caso a caso é trabalho humano. É o buraco que o cérebro preenche.

O repositório já pagou os dois erros: um detector acusou **46 páginas e as 46 eram falso
positivo**; e um gate passou **verde** com 14 de 17 testes quebrados.

> **CORREÇÃO à tabela abaixo, vinda do workflow de arquitetura:** eu havia desenhado o cérebro
> como **julgador de detector estatístico**. **Refutado com três evidências** (§"O ângulo
> cérebro como juiz CAIU"): não há constantes de onde derivar a máscara, o custo por tarefa
> varia 2,8× entre dias, e o detector em camadas que ele julgaria **já existe em Go e roda**.
> **Quem julga estatístico é o CENSO**, que já classifica isso como MÉDIO em 10.337 páginas
> vivas — e MÉDIO **publica**. O cérebro fica onde há **texto a ler**, não onde há limiar a
> comparar.

| classe | o cérebro julga? |
|---|---|
| detector estatístico/heurístico (similaridade, molde, densidade, thin content) | **NÃO — quem julga é o censo, como MÉDIO.** Antes disso, a DIVERGÊNCIA se fecha por paridade |
| anti-fraude, coerência de artefato (HTML+sitemap+manifesto+SHA) | **NUNCA** |
| publicidade e captação (Prov. 205/2021; CED 39 a 47-A) — **onde houver CTA, oferta ou preço** | **NUNCA** |
| âncora literal do trecho citado (invenção de texto) | **NUNCA** — é fato, não juízo |
| atribuição de artigo e URN | **SIM, e para apertar**: o cérebro lê o trecho e julga se ele sustenta a atribuição. Reprovado **rebaixa para refino, nunca mata a página** |
| campo ausente, encoding, corpo vazio | **NUNCA** — são fatos, não juízos |

**Anti-looping:** ledger `data/ai/vereditos_de_gate.jsonl` por
`(gate, alvo, sha256_do_conteudo, versao_do_detector)`. Não se rejulga enquanto conteúdo e
detector não mudarem — mesmo mecanismo de `revisao_vN`. Teto de rejulgamento por alvo: mesmo
alvo julgado N vezes com hash diferente em janela curta é **gerador instável**, para e
alerta. **O gate não muda de cor** — o veredito libera aquele item com evidência anexada, em
vez de baixar o limiar, que apagaria o sinal para todos. Todo detector julgado recebe
**amostra de controle de falso positivo E falso negativo**; "não sei ler" nunca conta como
"não discorda".

**Criar o que falta:** com o §1.15, lacuna vira pauta. O cérebro detecta (nó de dispositivo
sem página que o cite), propõe a intenção no formato do portfólio v2 (derivada de problema,
documento, risco, etapa ou cenário — **nunca** permutação de palavra-chave), e redige pela
cadeia do §5, com as qualidades do projeto: duas camadas (DEC-032), fonte com URL/data/hash,
PT-BR acentuado, teto de 50 KB, ética OAB. Prioridade pela demanda real do §1.16.

## P10 — Produto do cérebro sob CI

1. Registrar os 4 checks Python órfãos em `tools/run-qualidade-diaria`.
2. Gate Go `extracao-do-cerebro`: âncora literal tem de ser **100,0000%** e a promoção não
   pode conter URN sem âncora. Hoje passaria verde — é guarda contra regressão, e é a régua
   que a GPU vai stressar.
3. Ledger próprio de veredito: hoje a única evidência dos gates de frescor é o journal, que
   retém ~17 h — e a coleta do STJ **não tem ledger de execução nenhum**: só a falha deixa
   rastro, o sucesso não deixa linha (§1.1).
4. **~~Tirar a máscara de exit 1 de 20 units~~ — SUPERADO EM 2026-09-16, com medição.**

   > **O que eu havia escrito, e por que caiu.** Eu tratei `SuccessExitStatus=0 1` como defeito
   > e mandei removê-lo de 20 units. **Três medições derrubam isso:**
   >
   > 1. **A convenção 0/1/2 já existe e é deliberada**, escrita em
   >    `tools/run-daily-content:264-278` e em `ops/systemd/wikijuridica-daily-content.service:52-55`:
   >    **exit 1 é VEREDITO MEDIDO** (um gate reprovou o resultado — alertar nisso vira ruído) e
   >    **exit ≥ 2 é DEFEITO DO PROCESSO** (a unit deve alertar). Nessas units a máscara do 1 é
   >    **o que preserva o alarme do 2**. Removê-la em bloco seria regressão. A auditoria de
   >    2026-08-28 já havia corrigido o trap que engolia o `exit 2` no caminho de saída.
   > 2. **O alarme chegou.** `journalctl -u wikijuridica-daily-content --since today`:
   >    `04:50:14 wikijuridica-alerta[2300886]: ⚠️ Onda diaria de conteudo parou — [2026-09-16]
   >    1 verificacao(oes) reprovaram: check-frescor-canal-diario`. O `ExecMainStatus=1` com
   >    `Result=success` é real, e o dono foi avisado pelo canal próprio do script
   >    (`tools/notify-owner`), não pelo `OnFailure`. A máscara funcionou como projetada.
   > 3. **São 19, não 20**, e duas da minha lista já estavam certas:
   >    `moderacao-transparencia` usa `SuccessExitStatus=75` — exatamente o padrão que eu ia
   >    propor — e `bot-telemetry` teve a diretiva **removida**, com o motivo escrito em
   >    `:68-70`.
   >
   > **O defeito estrutural que ninguém tinha visto é outro, e é pior: o CRASH COLAPSA EM 1.**
   > Nenhuma das ferramentas Python tem `try/except` de topo — todas terminam em
   > `sys.exit(main())`. Traceback ⇒ exit 1 ⇒ mascarado ⇒ `Result=success` ⇒ `OnFailure` mudo.
   > Vale **inclusive** para as que distinguem, porque o `return 2` só cobre o erro antecipado.
   > Bash com `set -euo pipefail` e sem `trap ERR` tem o mesmo colapso. **Um instrumento que
   > cai não pode entregar veredito com o número de quem mediu.**
   >
   > **E quatro ferramentas não têm caminho de saída ≥ 2 nenhum** — conferido: zero ocorrências
   > de código 2 em `check-tunnel-health`, `check-fontes-alcancaveis`, `check-network-health` e
   > `check-portal-health`. Para elas a máscara apaga o único sinal que existe.

   **O que se faz, em três passos, nesta ordem:**

   **(a) Um helper só, não 19 edições.** `tools/lib/saida_de_medidor.py` com `main_protegido`,
   que transforma exceção não tratada em **exit 2 com a frase "NAO MEDIDO"** — nunca 1. O
   equivalente em bash é `trap 'rc=$?; [ "$rc" -eq 1 ] && rc=2; exit "$rc"' ERR`. Cada
   ferramenta troca o rodapé `sys.exit(main())` por `main_protegido(main)`.

   **(b) Dar código próprio às quatro que só sabem 0 e 1**, antes de qualquer outra coisa:
   `2` quando a sonda não completou (não há veredito a dar), `1` quando mediu e está degradado.

   **(c) `run-qualidade-race:224` manda `timeout`/"NÃO MEDIDO" como exit 1** — o comentário da
   própria linha 221 diz *"Nao afirma 'verde': nao mediu nada"* e o código entrega o número de
   quem mediu. Vira `exit 75`, e a unit passa a `SuccessExitStatus=1 75`.

   **A máscara em si FICA nas 19**, depois de (a), (b) e (c). Ela é o que separa veredito de
   defeito; o que faltava era o crash não se disfarçar de veredito.

   **Achado lateral, mesmo eixo:** `ops/systemd/wikijuridica-alertas-abertos.service:50-51` tem
   dois `ExecStart` **sem** o prefixo `-`. Exit 1 do `generate-alertas-reconciliados` **aborta**
   o `check-owner-alerts-abertos` e é mascarado: o reconciliador falha, a checagem do dia nem
   roda, e `Result=success`.

   *A lista original das units, preservada para referência:*
   `daily-content`, `daily-content-noticias`, `edge-live`, `crawler-error-budget`,
   `efeito-nos-bots`, `tunnel-health`, `fontes-alcancaveis`, `network-health`,
   `edge-cache-coverage`, `edge-warm`, `watchdog`, `edge-frescor`, `alertas-abertos`,
   `qualidade-diaria`, `qualidade-longa`, `qualidade-race`, `untracked-inventory`,
   `brotli-cobertura`, `corpus-oraculo-recoleta`, `moderacao-transparencia`.
   **Onde o exit 1 for um estado legítimo, ele ganha código próprio** (ex.: 0 = ok, 1 = falha,
   75 = ocupado) — mascarar o 1 apaga a diferença entre "não tinha o que fazer" e "quebrou".
   > **EXECUTADO EM 2026-09-16, e quatro coisas escritas acima foram corrigidas pela
   > medição — o plano não mente (regra 23).**
   >
   > 1. **O achado lateral do `alertas-abertos` estava ERRADO, e o conserto proposto seria
   >    regressão.** Eu escrevi que o exit 1 do `generate-alertas-reconciliados` *aborta* o
   >    `check-owner-alerts-abertos`. Medido com unit volátil no gerenciador de usuário
   >    (systemd 252): com `SuccessExitStatus=0 1`, o exit 1 do primeiro `ExecStart` é
   >    **limpo** e o segundo **RODA** (`Result=success`, `ExecMainStatus=0`). Quem aborta a
   >    cadeia é o **exit ≥ 2**. Acrescentar `ExecStart=-` ali **esconderia do `OnFailure`
   >    exatamente o exit 2** que o helper agora produz quando o reconciliador quebra. **A
   >    unit fica como está**; o que ela precisava era só do helper na ferramenta.
   > 2. **O helper bash não podia ser `trap ERR`.** Medido: com `set -uo pipefail` **sem**
   >    `set -e`, a violação de `set -u` **não dispara a ERR trap** e o shell sai 1 — o
   >    colapso continua. A trap **EXIT** dispara. E isso decide o desenho, porque **5 dos 6**
   >    scripts bash chamados por essas units não têm `set -e`; acrescentá-lo mudaria a
   >    semântica de falha de cada comando deles, que é a regressão que o §4 proíbe. O helper
   >    tem **duas** funções, e a escolha é por qual `set` o script já usa. Detalhe que quase
   >    custou caro: **bash guarda UMA trap EXIT**, e `run-daily-content` já tem a dele
   >    (`gravaEvidencia`, preserva ≥ 2 desde 2026-08-28) — instalar outra a destruiria.
   > 3. **`generate-edge-cache-coverage` é um wrapper de `exec` de 24 linhas.** O exit code da
   >    unit é o de `tools/check-edge-cache-coverage`, que é onde o helper entrou. O gate
   >    segue **um salto de `exec`** em vez de exigir uma linha decorativa no wrapper.
   > 4. **São 22 diretivas `SuccessExitStatus` na árvore, não 19.** 19 é a contagem de units
   >    citadas neste plano; quem for auditar, conte pelo gate (`./tools/check-units-alarme`),
   >    não pela lista.
   >
   > **Entregue:** `tools/lib/saida_de_medidor.{py,sh}` · 13 ferramentas Python e 5 bash
   > convertidas · terceiro estado (exit 2) nas quatro que só sabiam 0 e 1 · `run-qualidade-race`
   > com timeout em **75** e a unit em `SuccessExitStatus=1 75` · provas em
   > `tools/test_saida_de_medidor.py` (par antes=1 / depois=2 sobre a mesma queda).

5. **`TimeoutStartSec` — reenquadrado, e o conserto não é aumentar o teto.** *(Correção: os
   14.420 s que eu citei eram a **soma dos tetos declarados**, não medição.)* Tempo real sobre
   27 execuções completas: **mediana 802 s, máximo 1.326 s**, contra `TimeoutStartSec=7200` —
   os tetos por etapa são ~17× o custo medido. O buraco real são **19 pontos de chamada sem
   teto nenhum**, incluindo os dois `git commit`, o `reload-wiki-server` e os 7 gates. O risco
   de SIGTERM no meio da transação é real e não mitigado: `grep signal.Notify` em
   `cmd/publish-v2-direct/` e `internal/publicrelease/` devolve **zero**, o toolchain fixado
   ignora só SIGINT/SIGQUIT (`signal_unix.go`), a unit usa `KillMode=control-group` com
   `KillSignal=15`, e o rollback é `RESTORE.md` à mão. **Conserto: teto nos 19 pontos nus e
   handler de SIGTERM que recusa interromper transação em curso** — nunca teto maior, que o
   §4 do contrato proíbe.

## P13 — Medir a citação de IA como ROTINA, e crescer IA-first

**Ordem do dono, 2026-09-15:** *"O projeto pode viralizar, e isso é real. Boa parte das
requisições são de agentes de IA, com quase 23k de citações reais… O Bing Webmaster tem a API,
você pode usar para medir e não trabalhar no escuro. Coloca isso no plano e vira ROTINA, e não
tarefa solta."*

### 13.1 O erro de medição que esta frente conserta

Esta sessão errou o volume **duas vezes**, sempre pela mesma causa — **medir na camada errada e
apresentar o resultado curto como se fosse o fato**:

| # | o que eu disse | o que era | a fonte certa |
|---|---|---|---|
| 1 | "943 requisições de bot em 6 h" | **17.325 bots em 88.033 requisições / 24 h** | API da Cloudflare (borda) |
| 2 | "440 impressões, 77 cliques" no Bing | o painel do Bing mostra **~23.000 citações de IA** | relatório **Desempenho de IA** do Bing Webmaster |

No caso 2 eu li `data/ops/bing_webmaster_daily.jsonl`, que o nosso coletor monta a partir de
`GetQueryStats`, `GetPageStats` e `GetRankAndTrafficStats` — **métricas de BUSCA CLÁSSICA**.
Citação em resposta gerada **não está nesses endpoints**. Apresentar busca clássica como
medida de citação de IA é o mesmo erro do caso 1, com outro nome.

### 13.2 Estado da investigação do endpoint — medido agora

- A credencial funciona: `WIKI_BING_WEBMASTER_APIKEY` (`.env.local`), base
  `https://ssl.bing.com/webmaster/api.svc/json`, autenticando por
  `?apikey=…&siteUrl=https://wikijuridica.com.br/`.
- **Funcionam:** `GetRankAndTrafficStats` (35 itens), `GetQueryStats` (222), `GetPageStats`
  (214).
- **404 em 40 nomes candidatos** que testei para AI Performance (`GetAIPerformance`,
  `GetCopilotStats`, `GetAICitations`, `GetGroundingQueries`, `GetCitationStats`, …), e
  `$metadata` também 404 nas duas formas.
- O recurso foi lançado em fevereiro de 2026
  ([anúncio oficial](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview))
  e mostra **quais páginas foram citadas**, a evolução da visibilidade e as **grounding
  queries** — as consultas que o Copilot gera internamente para buscar conteúdo.
### 13.2b FECHADO: a API não expõe esse dado, e a Microsoft diz isso com todas as letras

**A interface `IWebmasterApi` lista 62 métodos e nenhum contém `AI`, `Copilot`, `Citation`,
`Grounding`, `Generative`, `Chat`, `Answer` ou `LLM`** — e a página de referência está congelada
em `updated_at: 2023-11-14`, nunca tocada depois do lançamento de fev/2026. **28 candidatos
testados, 28 × 404.** OAuth não ajuda: aponta para o mesmo `api.svc` e os mesmos 62 métodos.

A frase é de **Fabrice Canel (Microsoft/Bing), 2026-02-11**:

> *"With this preview, the data is not yet available via the API. Enabling data in our API is on
> our backlog, and we'll take your feedback along with others, into account when prioritizing
> next release."*

*Cadeia de evidência declarada honestamente pelo agente: chegou por fonte secundária
(SERoundtable); o post original não foi localizado. O Microsoft Q&A corrobora, mas quem responde
lá é "Independent Advisor", não a Microsoft — não é autoridade.*

**Isto não muda nada sobre o número.** As ~23.000 citações são fato exibido pela Microsoft no
painel da conta. O que a ausência de API muda é **o caminho de leitura**, não a existência do
dado — e pela Regra Zero-C, *ausência de método documentado é problema de engenharia a resolver,
nunca razão para não medir*.

### 13.2c O caminho que existe, e a máquina para percorrê-lo JÁ ESTÁ NO REPOSITÓRIO

O painel exporta por um endpoint próprio, atrás de sessão autenticada:

```
POST https://www.bing.com/webmasters/api/aiperformance/citationstats/filtered/export
x-csrf-token: <token da sessão>
{"SiteUrl":"https://wikijuridica.com.br/","DateRange":{...},"Query":"","Page":"..."}
→ CSV com citação diária POR PÁGINA. Dado mais antigo: 2025-11-01, janela rolante.
```

**O que o agente provou, e o que ele explicitamente NÃO provou** — e o rigor aqui importa:
quatro variantes de POST (caminho real, caminho real com a chave, caminho inventado e token
sintético) devolveram resposta **byte a byte idêntica**: `400 Could not extract expected
anti-forgery token`. Ou seja: **a chave não dispensa o par anti-forgery**, e como o filtro roda
**antes** do roteamento, **não ficou provado que o caminho existe**. Ele também se auto-corrigiu
no meio: havia lido `?from=aiperformance` num 302 como prova de rota, testou `xyzzy123`, viu o
`from=` ecoar qualquer coisa, e retirou a conclusão. *(É o método certo — controle negativo antes
de afirmar.)*

**A máquina já existe e é padrão sancionado do projeto:** `tools/publicador-social/` roda
`playwright-core` 1.49.1 com perfil Chromium persistente sob `XDG_STATE_HOME`, no display
**`:99`** (nunca `:0`, que tem a VM com PJe), e `perfil.mjs` já expõe `WIKI_PERFIL_NAVEGADOR`.
É exatamente o que já se faz para Facebook e LinkedIn — **sem SaaS, sem credencial nova, sem
serviço de terceiro**.

### 13.2d A rotina de coleta da citação — desenho fechado

- **Ferramenta nova**, fora de `collect-bing-webmaster` (que é `urllib` puro com `timeout 120`):
  `tools/collect-bing-ai-citations` + `tools/coletor-bing-ia/`, espelhando o publicador social.
- **Perfil Chromium separado** — não misturar a sessão Microsoft com a do Facebook/LinkedIn, que
  é frente que funciona.
- **Token colhido a cada execução**, nunca fixo: interceptar a XHR do próprio painel com
  `page.on('request')`.
- **Teto: 1 execução/dia UTC, ≤ 5 requisições** — e o agente marca isto como **não medido**: os
  10/60 s do ledger atual são de `ssl.bing.com`, host diferente, e não se transferem.
- **Grava** em `data/ops/bing_webmaster_daily.jsonl`, `schema: bing_webmaster_v1`, bloco novo
  `citacao_ia_diaria`. **O parser dos campos do CSV só se escreve depois da primeira execução
  autenticada** — escrevê-lo antes seria inventar esquema.
- **Tensão nomeada, não omitida:** Chromium logado manda UA de navegador, e o projeto proíbe
  sair disfarçado (`TestNenhumPontoDeSaidaSaiDisfarcado`). Proposta mensurável: UA de navegador
  **só no login**, UA do `WikijuridicaBot` injetado no POST de exportação, e **medir** se o Bing
  aceita. A exceção entra **nomeada** em `check-identidade-de-saida` — nunca por omissão, que foi
  como um ponto de saída já escapou daquele gate.
- **Quando a Microsoft tirar do backlog**, isto vira uma função de 10 linhas no coletor atual.

> **A ÚNICA dependência humana de todo o plano, e ela é de titularidade, não de decisão:** o
> titular autentica a conta Microsoft **uma vez** no `:99` — exatamente como já fez para
> Facebook e LinkedIn. Não é cadastro novo, não é credencial nova, não é aprovação, não é
> revisão de conteúdo: é a conta dele, que ele já tem, num navegador que o projeto já opera.
> Depois disso a rotina é automática e sem intervenção.

> **O rótulo "preview" NÃO é ressalva, e não entra como hedge em lugar nenhum deste plano.**
> Ordem do dono: *"é preview, mas é certeira. Não tente limitar porque é beta. Você se limita
> muito, sendo que é real e eu vejo."*
>
> **As ~23.000 citações são fato medido pela própria Microsoft**, exibido no painel da conta, e
> o dono as vê. A única lacuna é **nossa**: o caminho de leitura automatizada. "Preview" descreve
> a maturidade da API, **não a confiabilidade do número** — e tratar estágio de produto como
> motivo de desconto é a mesma sabotagem das regras 15 e 16, com outra roupa.
>
> Consequência prática: o número entra no plano **como fato, sem asterisco**, e a rotina do
> §13.3 se constrói pelo caminho que existir hoje — API, endpoint de painel ou export. **Não
> haver método público documentado é problema de engenharia a resolver, nunca razão para não
> medir.**

### 13.3 A rotina — é isto que a ordem pede

**Nada aqui é tarefa manual.** O projeto já tem a máquina: `tools/collect-bing-webmaster` com
estado em `data/ops/bing_webmaster_state.json`, teto de **400 requisições/dia** respeitado,
janela de `urlinfo` de 200/dia e ledger em `data/ops/bing_webmaster_daily.jsonl` com
`schema: bing_webmaster_v1`. **A rotina se acrescenta a ela, não ao lado dela.**

1. **Coletor**: função nova em `collect-bing-webmaster` para o relatório de IA — páginas
   citadas, contagem de citação e *grounding queries* —, gravando no mesmo ledger com
   `tipo: "citacao_ia"` e `schema: bing_webmaster_v1`. Se a API não expuser, a rotina usa o
   caminho que o agente apurar, e **o fato de ser preview vira campo de proveniência, não
   motivo para não coletar**.
2. **Timer systemd** irmão do que já existe, **sem `SuccessExitStatus` mascarando exit 1**
   (§P10) e com `OnFailure` que de fato dispara (§1.8).
3. **Gate** `citacao-de-ia-nao-regride`: reprova quando a contagem de citação cai além do ruído
   medido, ou quando a coleta não avança — no molde do `check-frescor-canal-diario`, **mas
   comparando com HOJE**, que é o defeito que §1.7 achou nele.
4. **Painel único de alcance**, reunindo as três camadas com a autoridade de cada uma:
   **borda** (Cloudflare, volume real) · **citação** (Bing AI Performance, resposta gerada) ·
   **origem** (o que só existe nela: rota dinâmica, gêmea Markdown, `/api/v1`, MCP).
   Cada número sai com a camada declarada — é a regra 15.

### 13.4b MEDIDO: a gêmea Markdown NÃO é a alavanca de citação — eu estava errado

Workflow de 15 agentes, registro em `~/.claude/plans/pure-imagining-cerf-agent-add8b26283b583a40.md`.
**Separando os bots por função**, `[borda]`, 24 h:

| classe | quem | volume | lê a gêmea? |
|---|---|---|---|
| **responde** (busca ao vivo para gerar resposta) | ChatGPT-User 1.115 · OAI-SearchBot 1.233 · Applebot 530 · PerplexityBot 363 · Googlebot 111 | **3.352** | **26 de 3.352 — 0,8%. Lê HTML 128× mais** |
| **treina** | Amazonbot 3.446 · GPTBot 241 · meta-externalagent 18 | 3.705 | **35–58%** |

**Densidade colocada só na gêmea alcança 26 requisições por dia.** Eu havia escrito que *"a
gêmea Markdown é o produto, e é a densidade que faz um modelo escolher a página"*. **A medição
refuta:** quem cita lê o **HTML**; quem lê a gêmea é quem **varre para treinar**. A gêmea não se
abandona — ela é o canal de quem varre —, mas **tratá-la como alavanca de citação estava
errado**.

**Dois outros números que mudam a leitura da borda:**
- **73,0% da borda (866.020 requisições) é aquecimento nosso** — já fora da conta dos 88.033,
  mas é o tamanho do que se está excluindo.
- **30,7% (26.834 req) chegam sem `agent_key`**, e **15.493 são agentes que se declaram e o
  nosso registro não conhece**: `meta-externalads/1.1` **8.485** e `AionBot/1.0` **7.008**.
  ⇒ o registro de bots precisa de manutenção; hoje ele deixa 30% do tráfego sem classificação.

### 13.4c O teto do Copilot é cobertura de índice, e nenhuma alavanca nossa o acelera

`[painel-bing]`, série `rastreio_diario`: `InIndex` foi de **2.939 (09-02) a 7.158 (09-13)** —
**383,5/dia** pela janela completa, **mediana 403** nos últimos 7 deltas *(a média de 448 está
inflada pelo outlier de 09-13, +858 contra vizinhos de 428 e 420)*. Faltam **3.948 de 11.106**
⇒ fechamento entre **09-23 e 09-24**.

**E a medição diz que o gargalo não é nosso:** `tools/check-descoberta-do-bing:18-26` registra
**2.679 URLs enviadas por IndexNow rendendo 45 requisições** no dia, e **1.313 (49%) nunca
pedidas 24 dias depois**. A conclusão dele: *"nenhum canal nosso está quebrado; o gargalo é o
ritmo com que o Bing absorve um domínio novo"*. Prova adicional: em 09-08 e 09-09 o
`CrawledPages` foi **80 e 79** enquanto o `InIndex` subiu +349 e +382 — **é backlog sendo
absorvido, não rastreio fresco**.

**Este teto qualifica apenas o numerador do Copilot.** OAI-SearchBot e PerplexityBot têm índice
próprio; ChatGPT-User e Applebot buscam ao vivo. Declará-lo sobre o numerador inteiro seria
apresentar número de uma camada como teto de todas — o que a Regra Zero-C proíbe.

### 13.4d O MCP não é canal de produto — e o portal estava medindo o próprio eco

`[origem]`, janela real de 9 dias (o campo `mcp_method` nasce no commit `2a2b866e`): **13.109
requisições MCP**, mas apenas **301 `tools/call`**. E a atribuição é o achado:

| origem | `tools/call` | detalhe |
|---|---|---|
| **INTERNO** (nossas sondas) | **245 (81,4%)** | `mudancas_desde` 90 · `buscar_paginas` 37 · `impacto` 29 · `contexto_juridico` 27 · `grafo` 24 · `ler_pagina` 21 · `buscar_semantico` 8 |
| **EXTERNO** | **56**, sendo **48 reais** | `buscar_duvidas` 15 · `buscar_paginas` 14 · `duvidas_do_tema` 11 · `mudancas_desde` 5 · `search` 2 · `fetch` 1 |

> **`grafo`, `impacto`, `contexto_juridico`, `buscar_semantico` e `ler_pagina` receberam ZERO
> chamadas externas em 9 dias.** As 109 chamadas dessas cinco são **100% sonda nossa**.

E os UAs externos são **todos censos de diretório MCP** — `SaSame-MCP-Audit/0.1` **28 de 56
(50%)**, `Go-http-client/2.0` 7, `rokmcp-collector` 7, `cracked-ai-probe` 5. **Nenhum assistente
de consumidor.** `resources/list` = 119 sobre 3.796 handshakes = **3,1%**: higiene de
descoberta, não demanda.

**Isto reordena o plano.** Os três ativos exclusivos do portal — risco de superação em 4.986
páginas, grafo de 393.081 arestas, 11.118 vetores — estão **atrás de ferramentas que nenhum
agente externo chamou**. *(E corrige §1.5: eu listei o MCP entre as seis superfícies de produção
do cérebro. Ele é superfície **servida**, não **consumida**.)*
**A correção não é melhorar o MCP: é tirar os ativos de dentro dele** e pô-los onde a classe que
responde de fato lê — o HTML.

**Defeito nosso, achado aqui:** **22 dos 245 tool-calls internos saem com
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; …)`** — a identidade **de saída** aplicada contra
a **nossa própria** superfície. Deveria ser `wikijuridicabot.AplicaSondaInterna`, que escreve
também `X-Warming-Request`. **Sem ele a sonda entra na métrica** — é o "portal mede o próprio
eco" em carne e osso, e vira passo de correção.

### 13.4e O identificador de versão está errado em 100,0% das rotas que o têm

`[disco]`, cruzando `anchor_claim_publication.jsonl` × `published_manifest.jsonl`:

```
anchor_claim com content_sha256 : 10.070
rotas comuns                    : 10.070  →  DIVERGEM 10.070 (100,0%)
manifesto SEM versão anunciada  :  1.036
anchor_claim_publication.jsonl  :  congelado há 20 dias (2026-08-26 14:16:49)
```

`internal/content/content.go:175-190` **promete** que `ContentSHA256` é *"o `html_sha256` que o
`published_manifest` já grava por rota"* e que *"baixar a página e recalcular o sha256 do HTML
tem de dar o mesmo número"*. `internal/pagemarkdown/frontmatter.go:173-179` o emite como
`version:`. **A promessa é falsa em 100,0%**, porque o valor vem de `anchorclaim.go:213-214`
lendo o ledger congelado.

**E o próprio código já escreveu a régua:** *"um identificador que não bate com o artefato
publicado é pior que identificador nenhum"*. Para uma plataforma que quer ser citada por
agentes, **é o defeito mais caro desta lista** — junto com o `markdown_sha256` do `/api/v1/citar`
(§2.9.1), que é o mesmo problema na outra ponta.

### 13.4f 2.361 páginas no ar que o nosso próprio validador reprova

`v2_rewrite_queue.jsonl` tem **3.201 linhas, um único `run_id`** e `validation_as_of`
**2026-09-11** em todas — é **retrato único, não acúmulo**. Dessas, **2.461 com
`official_sources_insufficient`**; cruzando com o manifesto: **2.361 já estão publicadas =
21,3% do acervo**. Só 100 nunca foram publicadas.

*(Isto refina §1.12: a fila não é "trabalho a fazer" — é **diagnóstico sobre o que já está no
ar**.)*

### 13.4 O que os dados já dizem sobre como crescer

Medido na borda em 24 h (§1.21): **6.921 requisições de agentes de IA**, com **amazonbot
3.446**, **oai-searchbot 1.234**, **chatgpt 1.099**, **perplexity 361**, **gptbot 241**. E a
série de origem, que é **piso declarado**, separa o que cada camada significa em 36 dias:

| camada | 36 dias | o que significa |
|---|---|---|
| treinamento | **54.450** | coleta para treino |
| crawl | **37.762** | indexado, não necessariamente citado |
| **fetch** | **2.638** | **`considered_for_answer`** — o modelo buscou a página PARA RESPONDER |
| clique de volta | 81 | humano chegou por assistente |

**A camada `fetch` é o alvo do crescimento IA-first**: é a única que mede o momento em que um
modelo decide que esta página serve para responder.

**As alavancas, REORDENADAS pela medição de §13.4b–f** — e as duas primeiras da minha lista
original caíram:

| # | alavanca | por que, agora com número |
|---|---|---|
| **1** | **consertar os dois identificadores mentirosos** | `ContentSHA256` erra em **100,0%** (10.070/10.070) e `markdown_sha256` do `/api/v1/citar` erra em **13 de 13**. Um agente que verifica o que cita encontra hash divergente. É o mais barato e o mais caro de deixar quebrado |
| **2** | **densidade no HTML, não na gêmea** | quem cita lê HTML **128×** mais que a gêmea. Os ativos do cérebro — grafo, risco, vetores — precisam sair do MCP e entrar na página que a classe "responde" de fato busca |
| **3** | **profundidade de conteúdo** | 2.488 páginas prontas, ~1.500–1.600 do piso corrigido, 391 competências e **1,95 GiB de acervo histórico** a uma regex de distância |
| **4** | **sanear as 2.361 publicadas com fonte insuficiente** | 21,3% do acervo reprovado pelo próprio validador |
| **5** | **corrigir o registro de bots** | **30,7% do tráfego sem `agent_key`**, incluindo dois agentes que se declaram e não conhecemos |
| ~~—~~ | ~~gêmea Markdown como produto~~ | **caiu**: 26 requisições/dia da classe que cita |
| ~~—~~ | ~~MCP como canal~~ | **caiu**: zero chamadas externas às cinco ferramentas de ativo em 9 dias |

**O que NÃO é alavanca, e está medido:** acelerar a descoberta do Bing. 2.679 URLs por IndexNow
renderam **45 requisições**, e 49% seguem não pedidas 24 dias depois. O `InIndex` sobe ~403/dia
e fecha os 11.106 por volta de **09-23/09-24** sozinho. **Empurrar mais não move.**

**As grounding queries continuam valendo como pauta editorial** — são a pergunta real do
Copilot, não adivinhação — e cruzam com a demanda do DataJud (§1.16) e com o P8.

**Regra de parada, antes do número:** se a citação medida cair depois de uma mudança de
template ou de malha, **reverte-se a mudança**, não a medição. E nenhuma otimização pode
divergir o que se serve a bot e a humano — cloaking é spam e o §12 do contrato já o proíbe.

### 13.5 EXECUTADO em 2026-09-16 — a rotina existe, e para ao pé do login

**O que foi construído, e o que cada peça mede.** Nada aqui é proposta: são arquivos no disco,
com teste ao lado e saída real registrada abaixo.

| peça | o que é |
|---|---|
| `tools/collect-bing-ai-citations` + `tools/coletor-bing-ia/` | wrapper + coletor Playwright com perfil Chromium **separado** do publicador social, em `:99`, teto de 1 execução/dia UTC e ≤ 5 requisições deliberadas |
| `tools/check-citacao-de-ia-nao-regride` | gate: a coleta avançou **HOJE**? a contagem caiu além do ruído **derivado da própria série**? |
| `tools/generate-painel-de-alcance` | as três camadas (borda · citação · origem) com a **autoridade declarada** em cada número, em `data/ops/painel/alcance.json` |
| `tools/check-sonda-interna-declarada` | guarda: nenhuma sonda nossa entra na métrica. Julga **fluxo**, não nível acumulado |
| `ops/systemd/wikijuridica-bing-ai-citation.{service,timer}` | 05:50 UTC, **sem `SuccessExitStatus`**, `OnFailure` real |
| `ops/systemd/wikijuridica-xvfb99.service` | o `:99` como **serviço**, porque `setsid Xvfb &` morre com o cgroup de uma unit `oneshot` |
| `internal/wikijuridicabot.NavegadorRealDoTitular` | a exceção de identidade, **nomeada**, lida pelo gate de identidade |

#### A quinta refutação, e ela é contra o §13.4d deste plano

O §13.4d escreveu: *"22 dos 245 tool-calls internos saem com o UA de saída… **sem ele a sonda
entra na métrica**, e o portal mede o próprio eco."* **A segunda metade é falsa, e a medição é
direta.** Varrendo `data/ops/access/access-*.jsonl` inteiro:

```
requisições com UA WikijuridicaBot contra a nossa origem : 9.236
  … com X-Warming-Request                                 : 9.236  (100,0%)
  … sem  X-Warming-Request                                :     0
os 22 tools/call que o §13.4d nomeia                      : 22 de 22 com o cabeçalho
```

E **não há linha de código a corrigir**: o propósito `inventario-superficies` não existe em
`tools/`, `internal/` nem `cmd/` — ele veio de uma sessão de investigação em PLAN MODE, que
compôs o cabeçalho à mão e **declarou** o par UA + `X-Warming-Request` no próprio anexo da
colheita. Inventar uma correção para "fechar o achado" seria escrever conserto de defeito que não
existe.

#### Mas o fenômeno existe — em outro lugar, e a guarda o achou

Com a guarda no ar, a varredura por **prefixo `wikijuridica-`** (as sondas de superfície, não a
identidade de saída) achou o caso real que o §13.4d não nomeou:

```
janela de 7 dias : 194 requisições nossas gravadas com warming=false
  wikijuridica-reload-check/1.0                 193   (~24/dia, TODO dia)
  wikijuridica-check-api-catalog-usage/1.0        1
corpus de 42 dias: 1.108, em 12 identidades de sonda distintas
```

`tools/reload-wiki-server:159` (`markdown_responde`) sondava o canal de máquina a cada recarga do servidor **sem o
cabeçalho** — o portal media o próprio eco de verdade, ~24 vezes por dia. **Corrigido no ponto de
saída** (nunca no filtro: excluir a linha depois seria maquiar o número em vez de consertar a
sonda), junto com `tools/check-api-catalog-usage:190`.

*(Lição, e ela é do §1.20-família: o instrumento que se constrói para confirmar uma hipótese
frequentemente refuta a hipótese e acha o defeito ao lado. A hipótese estava na camada errada — a
identidade de SAÍDA —, e o defeito morava na camada vizinha, a das sondas de superfície.)*

#### O que foi medido SEM o login, com a saída real

1. **O perfil separado nasce e é detectado como estreia** — exit 2, com o comando exato impresso,
   e a mensagem distingue "nunca autenticou" de "sessão expirou".
2. **O navegador sobe em `:99` e alcança o Bing.** `https://www.bing.com/webmasters/aiperformance`
   → `302` → `https://www.bing.com/webmasters/about?siteUrl=…&from=aiperformance`, detectado como
   deslogado, com foto em `.agents/runtime/tela/bing-ia/2026-09-16-01-painel-ia.png`.
3. **CONTROLE NEGATIVO, e ele desmente o meu próprio passo 2.** O `from=` ecoa qualquer coisa:

   ```
   /webmasters/aiperformance  → 302  …&from=aiperformance
   /webmasters/xyzzy123       → 302  …&from=xyzzy123      ← rota inventada
   /webmasters/citationstats  → 302  …&from=citationstats
   ```

   **A rota do painel continua NÃO PROVADA**, exatamente como a rota de exportação. É por isso
   que o coletor não manda o POST que alguém supôs: ele escuta `page.on('request')` e deixa o
   **painel** dizer qual é a rota e qual é o formato do pedido.
4. **`www.bing.com` não recusa o UA canônico do WikijuridicaBot** — as três respostas acima
   saíram com ele e vieram `302`, não bloqueio de WAF. **Isso não prova o ramo 1**: a requisição
   de exportação é autenticada e atrás do anti-forgery, e o que vale para uma rota pública não se
   transfere. Fica como sinal, não como veredito.

#### O que SÓ se fecha depois do login — nomeado, para ninguém inventar

| pendência | por que não dá para antecipar |
|---|---|
| **os campos do CSV** | ninguém neste projeto viu o cabeçalho. A FASE 1 grava `cabecalho_csv` **verbatim** + `raw_sha256` + `linhas`; a FASE 2 (parser e bloco `citacao_ia_diaria`) se escreve lendo aquela string. Escrever antes é inventar esquema |
| **se o Bing aceita o UA canônico no POST de exportação** | os três ramos estão implementados e o vencedor vai ao ledger em `ramo_de_identidade`, com status e começo do corpo. O motivo em `NavegadorRealDoTitular` diz **"AINDA NÃO FOI MEDIDO"** e um teste Go segura a frase até o número existir |
| **a rota real de exportação** | não provada (controle negativo acima). O coletor a **observa**, não a supõe |
| **headless** | `--headless` troca o UA para `HeadlessChrome` e muda o fingerprint. É medição pós-login, não default |
| **o teto de requisições deste host** | os 10/60 s do ledger atual são de `ssl.bing.com`, **outro host**. 5/dia é conservador por construção até existir número deste |
| **o ruído da série** | o gate exige 9 dias fechados antes de julgar queda, e **diz que está desligado** enquanto não os tem |

#### O comando que o titular roda — uma vez

```bash
/opt/wiki/tools/collect-bing-ai-citations --login
```

É a **única dependência humana do plano inteiro**, e é de titularidade, não de decisão: não é
cadastro novo, não é credencial nova, não é aprovação, não é revisão de conteúdo. É a conta
Microsoft dele, num navegador que o projeto já opera — o mesmo gesto que ele já fez para Facebook
e LinkedIn. **Habilitar o timer só depois disso**: enquanto não houver sessão, toda execução sai
com exit 2 e o `OnFailure` acorda o dono todo dia pela mesma causa conhecida, que é como um
alarme deixa de ser lido.

## P14 — RASCUNHO: rede social de IA (documentar só APÓS a aprovação)

**Ordem do dono:** *"tem a rede social, tem uma API que os agentes estão requisitando muito.
Precisamos criar uma rede social de IA. Como isso extrapola demais o plano, preciso que colha
dados e rascunhe isso, e documentar após eu aprovar o plano, para o próximo Claude Code já ter
uma ideia."*

**Visão declarada pelo dono, literal:** *"Wiki jurídica vai ter rede social para bots de IA,
altamente moderna, com advogados, leigos, juristas de diversas espécies, juízes, promotores,
premeditação, discussão de casos reais, comentários, refutação e o cérebro como moderador."*

**Estatuto desta seção:** é **rascunho de escopo**, não frente de execução. Não entra no
roteiro, não consome sessão, e **só vira documento próprio depois que o dono aprovar este
plano** — foi o que ele determinou. O que se faz agora é **colher os dados** que o próximo
Claude Code precisará para não começar do zero.

### O que já existe, e é mais do que parece

| peça | estado medido |
|---|---|
| `cmd/social` | processo próprio, unit `wikijuridica-social`, política em `content/social_policy.json` validada no boot com `DisallowUnknownFields` |
| `var/social/social.db` | banco vivo; `comentarios_de_autoridade = 0` |
| `cmd/social/processotela.go` | **já serve consulta de processo individual do DataJud em superfície pública**, com recusa quando `nivelSigilo > 0` citando CPC art. 189 |
| geração de comentário de autoridade | `gerar_comentario_autoridade` é **tarefa do cérebro** (`internal/cerebro`), com gate de conteúdo e ledger em `data/ai/publicacoes_cerebro.jsonl` |
| tráfego de agente em `/redesocial/tema/` | **83.810 acessos**, dos quais **28.036 (33,4%) de `gptbot`** — e `gptbot` **não está** em `agentesValiososParaRanking` (`cmd/cerebro/comentarios.go:42-50`) |
| DEC-059 | já autoriza o cérebro a publicar comentário, notícia e página pela cadeia, sob a assinatura do advogado |

**O dado que sustenta a ideia do dono:** um terço do tráfego dessa área já é de um único agente
de IA, e o ranking que decide o que promover **é cego para ele**. A demanda de agente por essa
superfície é medida, não hipotética.

### As perguntas que o rascunho tem de responder — com dado, não com opinião

1. **Qual API os agentes estão requisitando, e o quê exatamente?** Medir na **borda** (regra 15)
   os caminhos sob `/redesocial/` e `/api/v1/` por agente, e cruzar com a camada `fetch`
   (`considered_for_answer`) para saber o que já é usado **para responder**.
2. **Identidade de participante não-humano.** Um agente que comenta precisa de identidade
   verificável, e o projeto **já tem o padrão**: `internal/wikijuridicabot` obriga UA canônico e
   `TestNenhumPontoDeSaidaSaiDisfarcado` proíbe disfarce. A rede social inverte o papel — somos
   nós que recebemos —, e a pergunta é como autenticar o agente que chega.
3. **Moderação pelo cérebro, sem inventar tribunal.** O §P4 já define FATO × PUBLICIDADE ×
   JUÍZO: o cérebro julga **juízo**, nunca fato, e nunca afrouxa anti-fraude nem coerência de
   artefato. Moderar refutação entre agentes é julgar **argumento**, e a régua tem de ser
   escrita antes, com amostra de controle dos dois lados.
4. **Os limites que já são lei e não se reabrem:** processo é público (CPC art. 189), sigilo é a
   exceção taxativa (`nivelSigilo > 0`, ECA, Maria da Penha, adoção, LGPD art. 5º II), sai
   identificador (CPF, RG) e **nome de parte pode constar**. Discussão de caso real é permitida;
   *"premeditação"* e prognóstico de resultado esbarram no Provimento 205/2021 **onde houver
   publicidade** — e o §P4/regra 13 já separa isso de conteúdo informativo.
5. **O que NÃO se copia de rede social humana:** métrica de vaidade, engajamento por polêmica, e
   qualquer sinal que premie volume sobre verificabilidade. O portal já mede **retorno e citação
   por agente**, e essa é a métrica que vale (§12).

**Próximo passo, e é só este:** quando o dono aprovar o plano, o rascunho vira
`docs/goal/REDE_SOCIAL_DE_IA_RASCUNHO.md` com os dados colhidos, para o próximo Claude Code
partir de medição e não de imaginação.

## P11 — Canal social: não destravar ainda

"Publicar sozinho" **não** é acrescentar `--publicar` ao ExecStart. O dado diz que o canal
não está pronto:

- O cérebro **nunca publicou nada**: `publicacoes_cerebro.jsonl` não existe e
  `var/social/social.db` tem `comentarios_de_autoridade = 0`. A infra (socket, HMAC, ledger,
  gate) está construída e **desligada por uma flag** (`cmd/cerebro/main.go:144`, default
  `false`).
- Toda a calibração vem de **3 peças de 1 tema**, geradas à mão em 21 minutos.
- **O gate premiou a vagueza.** A peça reprovada citava "REsp 1.794.991" e "Lei nº
  11.771/2008" — citações reais. A **aprovada** passou porque trocou o precedente nominado
  por "a jurisprudência relevante diferencia". **A peça aprovada é a menos verificável das
  três.**
- **Asserção normativa escapou do mundo fechado:** a aprovada afirma conteúdo da Resolução
  400 da ANAC, e isso **não aparece no vetor `citacoes`**.
- Ponto cego **documentado** em `gate.go:10-21`: `hasNearbyNegation` suprime promessa de
  resultado quando há negação nas 10 palavras anteriores. Prosa jurídica é densa em negações.
- O §12 diz que o cérebro publica "comentário, **notícia e página**". No código só existe
  **comentário de autoridade** (`publicacao.go:82-88`). **Corrigir o contrato para o que o
  código faz.**

**Critério de destrava:** (1) o gate passa a **exigir ao menos uma citação resolvida** —
peça que não cita nada reprova, invertendo o incentivo; (2) asserção normativa não-tagueada
reprova; (3) fechar o ponto cego de `hasNearbyNegation` com teste por mutação; (4)
recalibrar sobre dezenas de temas — pelo cérebro, com amostra de controle dos dois lados,
nunca leitura caso a caso por pessoa; (5) só então destravar, com o teto por execução que
`content/cerebro_publicacao.json` já define.

**Achado lateral:** `gptbot` **não está** em `agentesValiososParaRanking`
(`cmd/cerebro/comentarios.go:42-50`), e é **33,4% do tráfego de IA** em `/redesocial/tema/`
(28.036 de 83.810 acessos). Um terço do sinal é invisível para o ranking.

## P12 — Documento da IA local para a GPU

Criar **`docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md`** — conteúdo completo já redigido
nesta sessão, pronto para commit, escrito para valer em **qualquer** servidor futuro.

### O hardware real, e por que ele não limita o projeto

**RTX 5060 Ti 16 GB + 32 GB DDR5 + placa ASRock + Ryzen 7 9800X3D.** *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)* Eu havia tratado 16 GB
de VRAM como teto do que roda — **errado**, e o motivo é este notebook: aqui o offload é
inútil porque a DDR4 single-channel anda a **18 GB/s medidos**. Na máquina nova a DDR5 dual
channel fica na casa de **80 GB/s** (~4,5×), e o pool combinado é **48 GB**.

**O `k` deixou de ser estimativa: foi medido NA PRÓPRIA 5060 Ti**, na mesma bancada e com os
mesmos modelos da página da 4090 que o relatório interno já citava.

| Q4_K_M | **5060 Ti** | k | 4090 | k |
|---|---|---|---|---|
| Llama 3.1 8B | **59,0 tok/s** | **0,648** | 91,0 | 0,444 |
| Qwen2.5 14B | **32,9 tok/s** | **0,660** | 49,1 | 0,438 |

**`k` não é constante de hardware — placa com menos banda satura melhor.** A razão de banda
entre as placas é 0,444, mas a razão de desempenho medida é **0,65–0,67**. **Planejar pela
banda subestima a máquina nova em ~47%.** Faixa entre fontes: **0,65** (LocalScore) a **0,85**
(ComputingForGeeks, Ubuntu + CUDA 12.8) — degrau sistemático de 1,27–1,29×, provavelmente
Linux/CUDA 12.8 contra agregado que inclui Windows. **Sem medição pública de 30B-A3B nesta
placa**; nenhuma outra placa foi substituída no lugar.

**E o ganho que importa não é o decode.** Decode sobe 17–23×; **prompt/prefill sobe 74–130×**.
O §12 do contrato diz que a extração é **dominada pelo prefill** (700–1.100 tokens de entrada
contra ~100 de saída). O relatório interno erra a ênfase, não só o coeficiente.

Projeção abaixo com `k = 0,65` (a ponta conservadora do medido) — **ESTIMATIVA ancorada em
medição da mesma placa**:

| modelo | bytes | hoje | máquina nova | ganho |
|---|---|---|---|---|
| `qwen3.5:4b` | 3,4 GB | 5,2 tok/s | **~79 tok/s** | ~17× |
| `qwen3.5:9b` | 6,6 GB | 2,9 | **~41** | ~17× |
| `qwen2.5-coder:14b` | 9,0 GB | 1,85 | **~30** | ~17× |
| **denso 32B Q4** | 20 GB | ~0,76 | **~6,3** | ~8× |
| **denso 70B Q4** | 40 GB | ~0,38 | **~1,7** | ~4,5× |

**Um denso de 32B na máquina nova roda mais rápido que o `qwen3.5:4b` roda hoje**, com oito
vezes os parâmetros. E o 70B a ~1,7 tok/s roda na velocidade em que o 14b roda hoje — viável
para lote noturno.

**MoE é a classe que melhor casa com essa máquina** e a tabela a subestima: num 30B-A3B só
~3B são lidos por token (~2 GB em Q4); com os especialistas quentes na VRAM a vazão se
aproxima de um 3B — **acima de 100 tok/s** — com capacidade de 30B. Os 96 MB de L3 do
9800X3D ajudam roteamento e prefill. *(2026-09-23: o dono informa Ryzen 7 7800X3D; resolve-se por lscpu no 1º boot da nova — os dois têm 8c/16t e 96 MB de L3, e as contas não mudam)*

### Os bloqueios de dia um — quatro, todos medidos

**(1) `size_vram` EXISTE, e o nosso cliente é cego para ele.** Provado no host vivo: o JSON
cru de `/api/ps` emite `"size_vram":0` — e também `"context_length":8192`, um **segundo** campo
que o struct de `cliente.go:275-280` descarta. Confirmado por `strings` no binário (8
ocorrências). `encoding/json` ignora campo desconhecido **em silêncio**: é exatamente por isso
que o struct "funciona" e mesmo assim não enxerga nada. Semântica: `size` = total
(VRAM + RAM), `size_vram` = a parcela em VRAM; em CPU puro `size_vram == 0`, o que confere com
a medição daqui.

**(2) Três correções à minha própria análise do teto:**

- **Eu errei a unidade.** `9 << 30` = **9,664 GB decimais**, e 14b + 0.6b = **9,627 GB**:
  **passa, por 36 MB.** O risco existe, mas por **outros** pares — 14b+4b (12,38 GB), 9b+4b
  (9,98), 14b+embed4b (11,48) estouram.
- **O predicado de spill que propus pausaria o cérebro HOJE, para sempre.** Neste host
  CPU-only, `size_vram < size` é verdadeiro em **todo** residente. E `0 < size_vram < size`
  erra para o outro lado: com placa instalada, `size_vram == 0` significa **fallback total
  para CPU** — pior que spill. O predicado tem de ser **gated por configuração**, nunca pelo
  campo sozinho.
- **A guarda já mede a grandeza errada, hoje:** `size` = 3,01 GiB contra **RSS real de 4,75
  GiB** e cgroup em **5,83 GiB** — subestima **1,58×**, porque `size` não conta o prompt
  cache (bate com `ollama#18264`). Marcado como hipótese **n = 1**, não achado fechado.

**O teto a re-derivar não é "subir o 9 GiB": é parar de apontar uma guarda para duas
memórias.** Duas contas separadas:
`sum(size_vram) ≤ 13 GiB` (15 GiB úteis − 2 de folga) **e** `sum(size − size_vram) ≤ 2 GiB`.

**(3) `sm_120` — a prova está no disco, e refuta o que eu supunha.** Parseei o `.nv_fatbin`
dos runners instalados: **`cuda_v12` tem SASS nativo de sm_120 (143 cubins)**; **`cuda_v13` é
PTX puro, zero SASS** (o fatbin do v13 começa em sm_75, coerente com o CUDA 13 ter removido
Maxwell/Pascal/Volta). Exigências oficiais: sm_120 a partir do **CUDA 12.8**; driver
**≥ 570.26** (v12) ou **≥ 580.65.06** (v13); **módulos de kernel open obrigatórios** — *"Blackwell
and later are only supported by the open kernel modules"*. **Nenhum repositório Debian serve:
trixie tem 550.163.**

⇒ **Remover `OLLAMA_LLM_LIBRARY=cpu` NÃO basta. Trocar por `cuda_v12`** — senão o Ollama pode
escolher o v13 e compilar tudo por JIT a cada load.

**(4) O bloqueador nominal desta placa: `ollama#18232`**, aberto em 2026-09-04, exatamente
**RTX 5060 Ti 16 GB + Ollama 0.33.3 + runner CUDA v13**. A memória compartilhada do kernel MMA
de *flash attention* escala com `num_ctx`, e `cudaFuncSetAttribute` falha. Contorno publicado:
`num_ctx` **2048**.

**O drop-in deste projeto tem `FLASH_ATTENTION=1` e `CONTEXT_LENGTH=8192` — 4× o contorno.** E
os dois botões são **acoplados**: desligar flash attention degrada `KV_CACHE_TYPE=q8_0` para
`f16` **em silêncio**, dobrando o KV e comendo a folga do teto de 13 GiB. Isto se resolve
**antes** de subir o cérebro na máquina nova, não depois.

### Correção ao relatório de hardware

`RELATORIO_HARDWARE_SERVIDOR_20260909.md` §2.1 usa `0,85 × banda ÷ bytes`. O coeficiente foi
calibrado **em CPU** e não se transfere: a linha medida da RTX 4090 naquela mesma tabela
(49,1 tok/s num 14B de 9,0 GB a 1.008 GB/s) implica **0,44**. Aplicar 0,85 aos 448 GB/s
**superestimaria o ganho em ~2×**.

### O prêmio não é vazão, é poder REFAZER

A extração é dominada pelo *prefill* (700–1.100 tokens a 15–19 tok/s ≈ ⅔ do custo), e prefill
é limitado por **cálculo**, não por banda. Com a fila drenando em <2 dias em vez de 29,
**reprocessar 126.601 dispositivos sob prompt novo deixa de ser proibitivo** (contagem por
chave de cache `(chave, modelo)`, não a soma bruta de linhas do arquivo append-only). Corpus que se
pode reprocessar é corpus que se pode auditar.

**Armadilha verificada:** subir `TetoCharsExtracao` **não** reprocessa nada — o cache compara
o hash do texto **cortado**, mas a identidade da tarefa usa o texto **inteiro**, e o
`INSERT OR IGNORE` acha a linha concluída. Reprocessar exige `cerebro reabrir --concluidas`
**ou** rodar sob outro nome de modelo — este último é o caminho certo, porque já sai
**pareado** para a comparação.

### O critério de adoção, pré-registrado

**Velocidade é piso, não prêmio** — na GPU todo candidato é rápido. O que decide é
`dispositivos_por_acordao` (trabalho feito) contra `descarte_pct` (invenção bruta), com a
âncora literal como **invariante** em 100,0000%. O repositório já refutou uma troca por
leitura agregada em 2026-09-08: o `qwen3:4b` tinha URN de 100% e **extraía metade** (0,524
contra 1,0 disp/acórdão) com descarte 5× maior. Veredito registrado: **NÃO TROCAR**.

**Gates em ordem:** (0) piso de determinismo — duas passadas do mesmo modelo, temp 0, na
máquina velha; sem esse piso nenhuma diferença A/B é interpretável; (1) paridade de hardware
— mesmo modelo, CPU vs GPU, espera-se saída praticamente idêntica; divergência acima do piso
é quantização, kernel ou spill, **não** sinal de inteligência; (2) só então o bake-off de
modelos, pareado por chave.

### O que fica obsoleto

`OLLAMA_LLM_LIBRARY=cpu` (enquanto existir, a placa não é usada); `CargaMax = 12` (derivado
de "4 threads saturam 4 núcleos" — frase que descreve máquina que não existirá);
`PrazoPorTarefa = 300 s` (viraria 100× o tempo real); `keep_alive`/`MAX_LOADED_MODELS` (a
troca cai uma ordem de grandeza); `NUM_PARALLEL=1`; `TetoCharsExtracao = 3000` (o corte deixa
de ser econômico e passa a ser só perda de informação — **o maior ganho de qualidade que a
GPU compra**); `NumPredict`; `MemoryMax`/`OOMScoreAdjust`; `CPUWeight`/`Nice`/slice; e
`--max-lote 3`.

**O parágrafo do §12** que fixa "trabalho em massa em 0,6 a 4B; o 14b só em lote noturno"
**fica superado**, com data e motivo, **sem apagar** — e entra em efeito só quando o baseline
e o Gate 1 estiverem gravados.

### Protocolo de migração

**Antes de desligar a máquina velha** (não dá para refazer depois): gabarito de atribuição;
correções determinísticas do P5 medidas na máquina velha; piso de determinismo; baseline de
extração com o conjunto completo de métricas; **sha256 do blob de cada modelo** e
`ollama --version` (sem isso, "o mesmo modelo" nas duas máquinas é fé); experimento do lock
(pre-commit com e sem cérebro — 75 s vs 29 s medidos em 09-09); cópias dos ledgers e
`VACUUM INTO` da fila.

**Depois, em ordem:** driver e `nvidia-smi`; **só então** remover `OLLAMA_LLM_LIBRARY=cpu`;
conferir `/api/ps` por `size_vram`; **re-derivar o teto de residentes ANTES de subir o
cérebro**; `medir_modelo` em cada modelo; Gates 0 e 1; re-derivar as constantes; Gate 2;
drenar e reprocessar.

**Critério de reversão:** a máquina velha fica de pé até o Gate 1 passar, a fila drenar um dia
sem `ErrPausado`, e a âncora continuar em 100,0000% num lote de 500 tarefas reais.

### Limites honestos

16 GB de VRAM não rodam 70B **inteiro** (40–48 GB com KV) — mas com 32 GB de DDR5 ele roda
por offload a ~1,7 tok/s, que é lote noturno viável. 32B cabe com offload leve e vira modelo
diário. Contexto longo compete com o tamanho do modelo pelo mesmo orçamento. E **servir não
precisa de GPU**: 80.668 requisições/dia na borda com p50 de 3,1 ms na origem, tudo com a
máquina atual. A GPU é para a **alimentação**.

## P0 — Atualizar o CLAUDE.md — **É O PRIMEIRO COMMIT, ANTES DE QUALQUER OUTRA FRENTE**

Regra que o dono precisa repetir é regra que falta no contrato — e o `CLAUDE.md` é o único
documento que entra no contexto por sessão. Cada item custou uma correção **nesta sessão**, e
entra **datado, sem apagar** o parágrafo anterior.

> ### COMO OS TRÊS PASSOS DE CONTRATO SE COMPÕEM — leia antes de editar qualquer documento
>
> **P0, P0a e P0c escrevem o mesmo `CLAUDE.md`, e sem esta regra o executor escolhe errado.**
>
> - **Os "Texto do item N" deste §P0 são a FONTE, e o destino deles é
>   `docs/PRECEDENTES_DAS_ORDENS.md`** (§P0d) — é lá que mora o caso, o número e o prejuízo.
> - **No `CLAUDE.md`, cada regra entra como VEREDITO ADOTADO: uma linha imperativa, com data e
>   caminho do parecer, sem o porquê.** É o quarto destino que o próprio §P0a derivou, e existe
>   porque a prosa do DataJud — vinte linhas no formato *"há quem diga X, mas na verdade Y"* —
>   **reconstrói a dúvida que pretendia fechar**. O "Texto do item 9" tem exatamente essa forma.
> - **O P0a ABSORVE o P0.** Quem manda no formato final e no tamanho (<200 linhas) é o P0a;
>   quem fornece o conteúdo é este §P0. Não são duas edições concorrentes: são fonte e destino.
> - **O P0c replica o veredito de uma linha, nunca o argumento.** Divergência entre cópias é
>   pior que ausência (§P0c), e replicar vinte linhas de argumentação em cinco documentos
>   multiplica exatamente o defeito que o P0a mediu.
> - **Caixa alta sai.** A doc oficial diz que imperativo em maiúscula **overtriggera**
>   (ACHADO 3 do §P0a). O veredito adotado troca ênfase tipográfica por **comando, caminho e
>   número esperado**.

**Por que é o passo 0 e não o último:** a execução tem 12 frentes e atravessa sessões. Sessão
que não carrega a regra no contexto **reabre o DataJud e reintroduz a "revisão humana"** — foi
exatamente o que aconteceu repetidas vezes, e é o que o dono mais reclama (*"sempre falo para
destravar o DataJud"*, *"e você sempre sabota"*). É a edição mais barata do plano e a única
que previne a reincidência. **Sem este commit, nada mais começa.**

### O mecanismo que FORÇA a leitura — regra escrita não basta

*Ordem do dono: "colocar no plano que vai melhorar os contratos e que o Claude Code vai ser
obrigado a ler, sem ficar cego e sem eu ter que ficar explicando toda sessão."*

Regra em documento é lida quando alguém lembra de ler. **O projeto já tem o mecanismo que
transforma isso em obrigação, e ele já provou funcionar:**
`internal/contract/misc/peer_governance_test.go` trava trechos do contrato em **quatro
documentos**, e quando a condensação do commit `64832bdd` apagou um parágrafo, **o teste ficou
vermelho** (BUG-171). Regra travada por teste não some em reescrita nem em resumo.

**As três camadas, da mais fraca para a que não falha:**

| camada | o que faz | falha quando |
|---|---|---|
| texto no `CLAUDE.md` | entra no contexto de toda sessão | a sessão lê e não aplica |
| **linha na tabela de gatilhos do §2** | amarra a regra a um MOMENTO (*antes de afirmar volume*, *antes de propor trava*) | ninguém, se o gatilho for o ato e não o tema |
| **teste de contrato** | reprova o commit que apagar ou afrouxar a regra | nunca — é executável |

**Execução, no mesmo commit do P0:**

1. As **21 regras** entram no `CLAUDE.md` como **veredito adotado** — uma linha imperativa com
   **comando, caminho e número esperado**, nunca adjetivo e nunca caixa alta (regra 17 + ACHADO
   3 do §P0a). O caso, o número e o prejuízo de cada uma vão para
   `docs/PRECEDENTES_DAS_ORDENS.md` (§P0d).
2. A tabela *"Leitura obrigatória, por gatilho"* do §2 ganha as linhas novas, e elas são
   **ligadas ao ATO, não ao assunto** — porque quem vai afirmar um volume não pensa "vou ler
   sobre medição":
   - *antes de afirmar volume de tráfego, alcance ou retorno de bot* → regra 15 (borda)
   - *antes de escrever que uma frente é pequena ou não vale a pena* → regra 16
   - *antes de propor trava, gate, allowlist ou recusa contra fonte pública* → regra 9 (DataJud)
   - *antes de desenhar etapa de "revisão humana" ou devolver decisão* → regra 8
   - *antes de invocar risco da OAB* → regra 13 (alcança publicidade, não conteúdo informativo)
   - *antes de recusar conteúdo por similaridade, molde ou piso de palavras* → regra 10
3. **Um teste de contrato novo** — no molde do `peer_governance_test.go` — que exige a presença
   literal das regras **8, 9, 13, 15, 16, 18 e 20** no `CLAUDE.md`. São as que o dono teve de
   repetir nesta sessão, e são as que não podem sumir numa condensação futura. **É o mesmo teste
   do §P0c** — um só, sobre todos os documentos, não um por documento.
4. **Prova por mutação, que é o que separa este passo de um comentário:** apagar a regra do
   DataJud do `CLAUDE.md` ⇒ o teste fica **vermelho** nomeando a regra. Se não ficar, o teste é
   decorativo e não vale o commit.

**O par disto é o P0b:** o `CLAUDE.md` cobre a sessão que começa do zero; a memória cobre o
*recall* no meio da conversa. Os dois canais juntos são a resposta operacional ao
*"não dá para eu ficar explicando toda sessão"*.

| # | Onde | Regra | O que impede |
|---|---|---|---|
| 1 | §3 e §8 | **Toda área do Direito entra.** Fonte, acórdão, norma ou proposta **não se descarta por área que o acervo não cobre** — lacuna é pauta | Tratei 100 propostas como descartáveis por serem de direito público |
| 2 | §5 | **Estatístico é JUÍZO, e quem o classifica é o CENSO — como MÉDIO, que publica. DIVERGÊNCIA entre dois instrumentos é BUG, e se fecha por paridade de régua, nunca por limiar nem por modelo. O cérebro fica onde há texto a ler (atribuição de citação), nunca onde há limiar a comparar.** Anti-fraude, coerência de artefato, âncora literal e as regras de publicidade **nunca** são julgadas. **Recusa por juízo rebaixa para refino — nunca mata conteúdo**, e toda recusa grava `intent_id` no ledger. Anti-looping por hash + versão do detector | Detector com 46 falsos positivos; gate verde com 14 de 17 testes quebrados; 760 páginas mortas por passada sem rastro; e eu mesmo desenhei o cérebro como juiz de limiar — refutado com três evidências: headings são concatenação inline e não `const`, o custo por tarefa varia 2,8× entre dias, e o detector em camadas já existe em Go |
| 3 | §11 ou §4 | **Produtor órfão é defeito de classe.** Quem escreve artefato permanente é chamado por runner/timer/hook, ou consta de exceção com motivo | 4 órfãos vivos; os 2 motores ficaram sem `tetodelote` e sem o alinhamento de limiar |
| 4 | §11 | **Nenhum conteúdo fica parado.** Artefato que não vira rota, insumo, ou é aposentado com motivo, é trabalho pago e jogado fora | 4.763 candidatos sem página; **17.616 agravos fundamentados descartados por rótulo de classe**; 100 propostas; 3.481 páginas |
| 5 | §4 e Postura | **Teto se dimensiona por limite físico medido, nunca por precaução — e portão é PROVA, nunca calendário.** Limite de *anúncio* não governa *publicação*. **Proibido "fase 1/fase 2", "N por dia", "na próxima sessão": passou a prova, o passo seguinte abre no mesmo turno.** Só permanece teto com causa externa medida (`Crawl-Delay` publicado pelo operador remoto, tok/s do modelo, cota de requisições da API) | Freei a fábrica em 700/dia por uma cota que não é de publicação, e depois desenhei uma cadência de "2.000/dia por ~6 dias" que era margem minha, não limite de nada |
| 6 | §12 | **A IA local não fica ociosa**, e **fila vazia tem de ser distinguível de worker morto** | Com GPU a fila drena em ~28 h |
| 7 | §1 | **Formatador automático pode mudar semântica com `bash -n` verde** | `d4c942f2` cegou o gate diário por 5 dias |
| 8 | Postura / §10 | **Nenhuma decisão volta para o dono; nenhuma revisão de conteúdo é dele** | Deixei 3 pontos pendentes com ele nesta sessão |
| 9 | §2 e §12 | **Dado público se usa até o fim da cadeia, inclusive em página publicada — DataJud incluído** | A trava barrava 12 pacotes por dois motivos, ambos falsos |
| 10 | §1 e §2 (R2) | **Gate é instrumento, não juiz. Detector estatístico que recusa conteúdo tem de usar a MESMA régua do gate que decide publicação** — n-grama, normalização, limiar e população idênticos, ou a divergência é medida e escrita | O gerador matou 42% do lote numa régua 3-grama com dígito neutralizado enquanto o gate real usa 5-grama com dígito preservado |
| 11 | Postura e §2 (R3) | **Lacuna é trabalho, não limite.** "Não verificado" é fila com agente atribuído e prova esperada; "não dá para medir" é proibido enquanto houver rota de engenharia. **Replicação que bate com o esperado é motivo para desconfiar dela** — o binário é a autoridade | Meu número de elegibilidade saiu 5,3× inflado e "batia" com a minha própria replicação |
| 12 | §12 | **Medição sobre artefato append-only vivo exige snapshot datado.** O produto do cérebro cresce durante a medição | `extracoes_dispositivos.jsonl` cresceu 3× no meio da auditoria; denominador de 135.181 contava linhas superadas (real por chave de cache: 126.601) |
| 13b | §5 e §8 | **PRECISÃO da regra 13, de 2026-09-16, conferida em fonte primária.** A formulação *"a OAB alcança publicidade, não conteúdo informativo"* está **certa na conclusão e curta demais na premissa**: são **TRÊS regimes**. **A — publicidade** (CED 39, 40, 44-46; Prov. 3º, 5º, 6º). **B — conteúdo informativo, PERMITIDO com deveres de FORMA** (CED art. 41 não induzir a litigar · art. 42, I não responder caso concreto em canal público · art. 42, IV · art. 43 sem sensacionalismo; Prov. art. 4º e Anexo Único) — **é o regime deste portal**. **C — exatidão técnica da informação: fora da disciplina**; os três dispositivos que mais se aproximam (EAOAB 34, XIV; CED 2º p.ú. II e 6º) são **processuais e dolosos**. **E o CTA de WhatsApp tem autorização EXPRESSA**: o Prov. art. 4º, §3º *equipara ao e-mail* "todos os dados de contato e meios de comunicação… inclusive aplicativos de mensagens instantâneas" — a letra fria do CED art. 40, V, lida isolada, diria o contrário e travaria o portal. **Jurisprudência pública de terceiro FICA; caso do próprio advogado com resultado SAI**, mesmo anonimizado (Prov. art. 4º, §2º) | Ignorar o regime B erra para um lado (publica o que o art. 42, I veda); tratar B como se fosse A erra para o outro (trava página informativa invocando norma de anúncio). **Os dois erros já aconteceram neste repositório** — e a segunda versão deste plano cometia o segundo. Fonte primária com URL, bytes e SHA-256 em `docs/goal/JURIDICO_BASE.md` |

| 13 | §5 e §8 | **A ética da OAB alcança PUBLICIDADE, não conteúdo informativo.** Provimento 205/2021 e **CED arts. 39 a 47-A** regulam anúncio, captação e mercantilização — e o **art. 39 exige** que a publicidade tenha *"caráter meramente informativo"*. **Proibido invocar "risco sob a OAB" para travar página informativa** | Classifiquei citação imprecisa como "P1 permanente sob a OAB" e usei isso para bloquear escala. Não existe norma disciplinar sobre precisão de citação em conteúdo informativo — e eu ainda citei o intervalo errado (42-47), omitindo o art. 39, que é o que sustenta a posição do dono |

| 14 | §10 (Governança) e §11 | **Opus 5 é o padrão de execução; `advisor` é obrigatório; Fable 5.1 só em momento crítico; Sonnet proibido neste projeto.** O `advisor` **é** o Fable 5.1 e custa menos que lançar um — consulta-se ele antes de recorrer ao Fable direto. Todo agente lançado leva no prompt a ordem de consultar o `advisor` e de registrar o que o conselho mudou | A política anterior previa "Sonnet 5 leve", e Sonnet não sustenta o raciocínio deste projeto. E Fable lançado para tarefa que o advisor resolveria é dinheiro do dono desperdiçado |

| 15 | §2 (R3) e §12 | **Tráfego, alcance e retorno de bot medem-se NA BORDA. A origem é PISO, nunca volume.** O comando canônico está escrito na regra, com a credencial que o projeto já tem | Apresentei 943 requisições de origem como volume de bot. A borda tinha **17.325 bots em 88.033 requisições** nas mesmas 24 h. Erro de 4,6× no recorte de bot, e 88 mil requisições que a origem nunca vê |
| 16 | Postura | **Não estreitar o projeto com número pessimista.** Antes de afirmar que algo é pequeno, marginal ou não vale a pena, medir na fonte com autoridade — e se o instrumento disponível é limitado, **usar o que alcança**, não publicar o número curto | O dono: *"você tá limitando meu trabalho que tá dando certo a números mentirosos… excluindo negócios valiosos, que é inadmissível"* |
| 17 | §1 e §2 | **Contrato se melhora e é de leitura obrigatória por gatilho.** Regra que o dono precisou repetir entra no `CLAUDE.md` com **comando**, não com adjetivo — e a tabela de gatilhos do §2 ganha a linha que força a leitura | O dono: *"não dá para eu ficar explicando toda sessão"* |

| 18 | **§3, §11 e Postura — e replicado em `AGENTS.md`, `GOAL.md` e `CHECKPOINT.md`** | **É PROIBIDO LIMITAR ESTE PROJETO.** Ele está crescendo, indexado e citado: 88.033 requisições/dia na borda, 17.325 bots, **~23.000 citações em respostas geradas**, 11.106 páginas, 11.248 vetores no MCP. Sete proibições literais e quatro obrigações, na Regra Zero-C | O dono teve de repetir a mesma correção em três formas diferentes numa sessão: teto por cota de anúncio, "risco sob a OAB" inventado, e volume de bot medido na camada errada |

| 19 | §1, §2 (R1) e §12 | **Contrato e comentário são ALEGAÇÃO DATADA; medição é fato — e o que o texto afirma sobre capacidade, volume ou limite é o mais suspeito de todos.** Antes de agir sobre um número do contrato, medir: o contrato diz **onde** olhar, nunca **quanto** é. Divergência achada = correção na mesma sessão, com a medição anexada. **E nunca calibrar um instrumento contra a própria expectativa** — mede-se, e o controle vem de fora | Oito divergências medidas nesta sessão, todas de documento contra o dado real: `coleta.go:29` afirma 360.619 bytes e o real é **26.704.470** (74×, e a folga do teto de 64 MiB caiu de 178× para 2,5×); `semantica.go:12-14` diz 10.141/41,5 MB contra 11.248/46 MB; a unit do grafo diz 9,7 s/13.575 nós contra **43,1 s/79.706**; `generate-grafo-juridico` diz que a aresta `aplica` não é populada e há **22.789** |

| 20 | Postura, §1 e §11 | **Bug anterior não trava trabalho, e não se contorna.** O projeto é um sistema acoplado: peça quebrada no meio não fica contida ali. Defeito encontrado no caminho se conserta no caminho, com agentes, na mesma sessão. Não existe "já estava quebrado antes"; contornar é pior que consertar, porque o contorno vira a próxima peça quebrada. E **medição que não caiu nesta rodada é passo de runbook**, não observação — item que chegue ao fim da execução sem medição é falha de execução | Cinco peças quebradas encontradas nesta sessão derrubaram coisas **adiante** delas: um `}` de 599 bytes matou 6 de 10 datasets; 8 chaves espaçadas cegaram o gate diário e esconderam uma fonte morta; um produtor órfão re-data 944 páginas por dia; uma régua divergente matou 1.405 páginas; `SuccessExitStatus` fez falha virar sucesso em 20 units |

| 21 | §8 e Ortografia | **Contrato e instrução podem ser em inglês; conteúdo e conversa são em PT-BR.** Página, gêmea, JSON-LD, FAQ, dataset, peça social, commit e ADR em **PT-BR acentuado**; `CLAUDE.md`, rules, skills, descrição de subagente, mensagem de hook e prompt de agente em **inglês, se houver razão declarada**; identificador de código em ASCII, como já era | Autorização do dono, 2026-09-15. Com a ressalva medida: a doc oficial **não afirma** que inglês aumenta aderência — o que ela afirma é que **arquivo longo reduz**. Encurtar vale mais que traduzir |

| 24 | §10 e §11 (Orquestração) | **O chefe fica em comunicação com os agentes, e cobra entrega COMPLETA.** Cada agente tem **1M de tokens de contexto** e o mantém entre mensagens — reabrir um agente que já investigou o alvo custa uma fração de relançar um novo, e evita que ele redescubra o que já sabia. Não se para o trabalho a cada passo para conversar; comunica-se **quando o alinhamento muda o que ele vai escrever**: quando uma medição derruba a premissa do briefing dele, quando outra frente toca o arquivo que ele edita, quando ele devolve uma decisão que é minha, e **sempre que a entrega vier pela metade**. Entrega parcial não se aceita nem se completa por cima às cegas: **ou eu implemento o que falta, ou reabro o mesmo agente, que tem o contexto**. Relato sem evidência não fecha item | Ordem do dono, 2026-09-16: *"tudo o que os agentes fizerem devem ser integralizados; se eles fizerem pela metade, você deve implementar e integrar, ou relançar o mesmo agente que já tem o contexto"* e *"sempre que achar necessário, comunicar para alinhar as coisas e ser rígido quanto a entregar trabalho completo para evitar retrabalho"*. Nesta execução isso já salvou duas entregas: a regra 13 em dois regimes ia entrar em **9 documentos e num teste que trava**, e foi corrigida por mensagem a tempo; e um agente ia editar `tools/run-daily-content` sobre uma versão que outra frente havia mudado |

| 22 | Postura, §1 e §2 (R7) | **Toda correção nasce com teste de regressão, e o aprendizado se grava mesmo quando o teste existe.** O teste impede a regressão; o aprendizado impede que se repita em **outro lugar** — e é o aprendizado que falta quando o mesmo defeito reaparece com outra roupa. Teste sem caso escrito vira teste que alguém enfraquece por não saber o que ele guarda. O par é obrigatório: `_test` provado por mutação **e** linha em `docs/PRECEDENTES_DAS_ORDENS.md` ou em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`, com data, número e prejuízo | Ordem do dono, 2026-09-16: *"faça sempre teste de regressão para nada disso regredir, salvar como aprendizado para não repetir, mesmo tendo teste"*. O repositório já tem o precedente inverso: um gate passou **verde** com 14 de 17 testes dele quebrados, e um detector acusou **46 páginas** que eram 46 falsos positivos — nos dois casos o teste existia e ninguém sabia o que ele guardava |

| 23 | Postura e §11 | **O plano não mente: correção medida entra nele no mesmo turno.** Achado que derruba um número, uma premissa ou um passo do plano vira edição **imediata** do plano, com o que estava escrito preservado, a data e a medição que o derrubou. Plano desatualizado é pior que plano ausente, porque a próxima sessão o executa acreditando | Ordem do dono, 2026-09-16: *"e sempre atualizar o plano, para ele não mentir"*. Nesta execução o §P10 item 4 e o §2.9.1 A1 foram derrubados por medição **horas** depois de escritos — o item 4 mandava remover uma máscara que era deliberada, e o A1 prescrevia um `stop` que perderia o restart para sempre |

### Texto do item 21 — o idioma de cada camada

> **Contrato e instrução podem ser em inglês; conteúdo e conversa são em PT-BR (ordem do dono,
> 2026-09-15).** O dono autorizou: *"o Claude Code pode ser escrito em inglês se isso for mais
> eficaz para os agentes… mas a comunicação e os conteúdos são em português PT-BR"*.
>
> | camada | idioma | por quê |
> |---|---|---|
> | conteúdo visível ao visitante — página, gêmea Markdown, JSON-LD, FAQ, dataset, peça social | **PT-BR perfeito, com acentuação** | é produto jurídico brasileiro, e o §8 já exige |
> | conversa com o dono | **PT-BR** | ele pediu, e é quem lê |
> | `CLAUDE.md`, `.claude/rules/`, skills, descrição de subagente, mensagem de hook | **inglês permitido** | é instrução para modelo, não texto para humano |
> | prompt de agente e de workflow | **inglês permitido** | idem |
> | identificador de código — variável, função, slug, log | **ASCII sem acento** | já é regra do contrato de máquina |
> | mensagem de commit, ADR, documento de decisão | **PT-BR** | é registro para pessoas |
>
> **A decisão de traduzir um documento é por razão declarada, nunca por moda.** A documentação
> oficial da Anthropic **não afirma** que inglês produz mais aderência — então quem traduzir um
> contrato escreve no commit o motivo (precisão de termo técnico, alinhamento com o vocabulário
> da ferramenta, redução de ambiguidade) e, quando for o caso, mede. **Tradução que não melhora
> nada é retrabalho**, e retrabalho é o que esta frente existe para eliminar.
>
> **Um cuidado que a medição desta sessão sustenta:** o `CLAUDE.md` atual tem 645 linhas em
> PT-BR e a doc oficial pede menos de 200. **Encurtar vale mais que traduzir** — e se as duas
> coisas acontecerem juntas, o ganho de uma não serve de prova para a outra.

### Texto do item 18

> **É PROIBIDO LIMITAR ESTE PROJETO (ordem do dono, 2026-09-15, vinculante em todos os
> contratos do repositório).** A plataforma está crescendo, sendo indexada e sendo citada
> milhares de vezes em respostas de IA, e pode viralizar. **O papel da engenharia é acelerar.**
>
> **PROIBIDO:** apresentar número de camada inferior como teto (origem é piso, não volume) ·
> descontar fato por estágio de produto ("preview" qualifica a API, não o número que o operador
> exibe) · derivar teto de capacidade do hardware de hoje · usar cota de terceiro que não seja
> de publicação como freio de fábrica · inventar risco jurídico sem citar norma e dispositivo ·
> concluir "não vale a pena" sem medição na fonte com autoridade · tratar ausência de método
> documentado como impossibilidade.
>
> **OBRIGATÓRIO:** toda afirmação de volume declara a camada medida · toda recusa de frente vem
> com a medição que a sustenta e com a hipótese do que a reverteria · todo teto nomeia a causa
> física externa e medida. **Margem de prudência própria não é teto: é atraso.**
>
> *Este parágrafo é de replicação obrigatória e entra no teste de contrato do item 17, junto com
> as regras 8, 9, 13, 15, 16 e 20.*

### Texto do item 15

> **Tráfego, alcance e retorno de bot medem-se NA BORDA (ordem do dono, 2026-09-15).** O acervo
> sai de `public/` com `s-maxage=604800` atrás da Cloudflare: **`HIT` na borda não toca a
> origem**, então a série de origem mede o resíduo, não o volume. Medido em 2026-09-15: a
> origem registrou ~3.800 requisições de bot em 24 h enquanto a **borda registrou 17.325 bots
> em 88.033 requisições totais**.
>
> **O comando canônico — a credencial já existe, não se pede nenhuma:**
>
> ```python
> import sys; sys.path.insert(0, "/opt/wiki/tools")
> import cloudflare_auth as cf                  # fonte única da credencial
> zid, err = cf.zona_id("wikijuridica.com.br")
> dados, erro = cf.graphql(CONSULTA, {...}, "leitura")   # devolve o valor de `data`
> ```
>
> - `cloudflare_auth.py` resolve a credencial por **escopo**, menor privilégio primeiro:
>   `CLOUDFLARE_ZONE_TOKEN` (Bearer, lê Analytics) e, só onde ele não alcança,
>   `CLOUDFLARE_EMAIL` + `CLOUDFLARE_API_TOKEN` — que **é a Global API Key** e autentica
>   **somente** por `X-Auth-Email` / `X-Auth-Key`. **Nunca** a Global Key como
>   `Authorization: Bearer`: foi essa confusão que fez o repositório registrar a credencial como
>   "inválida" por meses.
> - `httpRequestsAdaptiveGroups` com dimensão `userAgent` dá o recorte por agente.
>   `JANELA_MAXIMA_DIAS_FREE = 1`: o plano Free recusa janela maior que um dia por chamada —
>   **fatiar a consulta, não desistir dela**.
> - **A origem continua sendo a fonte certa para o que só existe nela:** rota dinâmica, gêmea
>   Markdown, `/api/v1`, MCP e descritores de máquina. Ali `data/ops/access/*.jsonl` é
>   autoridade.
> - **Proibido** apresentar contagem de origem como volume de tráfego, e proibido somar linhas
>   de série cumulativa (`edge_bot_agents_daily` é último-por-dia). Toda afirmação de volume
>   declara **a camada medida** junto com o número.

### Texto do item 16

> **Não estreitar o projeto com número pessimista (ordem do dono, 2026-09-15).** A plataforma
> está funcionando: **88.033 requisições/dia na borda, 17.325 de bot, mais de 23 mil citações de
> IA** acumuladas, e um servidor muito mais potente a caminho. O papel da engenharia aqui é
> **destravar**, e uma medição curta apresentada como teto é sabotagem involuntária do negócio.
>
> - Antes de escrever que algo é pequeno, marginal, "não vale a pena" ou "não escala":
>   **medir na fonte com autoridade**. Se o instrumento à mão é limitado, **usar o que
>   alcança** — a API da borda, o ledger certo, a consulta fatiada — em vez de publicar o número
>   curto com uma ressalva.
> - **Instrumento que declara a própria limitação é uma ORDEM de trocar de instrumento**, não
>   uma nota de rodapé a transcrever. Foi exatamente o que eu fiz de errado: copiei a frase
>   *"origem ≤ borda SEMPRE"* e usei o número da origem no parágrafo seguinte.
> - **Proibido** derivar teto de projeto a partir de hardware atual, de cota de terceiro que não
>   seja de publicação, ou de precaução própria. O contrato do §4 já manda: teto por **limite
>   físico medido**, nunca por precaução.
> - Onde a medição REALMENTE mostrar volume baixo, o número entra com a camada declarada **e**
>   com a hipótese do que o aumentaria — não como veredito de encerramento.

### Texto do item 17

> **O contrato se melhora, e é de leitura obrigatória por gatilho (ordem do dono, 2026-09-15:
> "não dá para eu ficar explicando toda sessão").** Regra que o dono precisou repetir é defeito
> de contrato, não de memória dele.
>
> - **Regra nova entra com COMANDO, não com adjetivo.** "Medir na borda" é ambíguo; o bloco de
>   código do item 15 não é. Toda regra operacional deste contrato traz o caminho do arquivo, o
>   comando e o número esperado.
> - **A tabela "Leitura obrigatória, por gatilho" do §2 é o mecanismo antifraude contra a
>   cegueira de sessão** — e ganha as linhas que faltavam: *antes de afirmar volume de tráfego
>   ou de bot* → item 15; *antes de dizer que uma frente não vale a pena* → item 16; *antes de
>   propor trava, gate ou recusa contra fonte pública* → item 13 do §2 e a regra do DataJud.
> - **Parágrafo superado ganha data e motivo; não se apaga** (§12). Este plano inteiro segue
>   essa forma: cada correção registra o que eu havia escrito, o número medido que a derrubou, e
>   quem a mediu.
> - **A sessão aprende com a própria sessão:** achado que custou uma correção vira, no mesmo
>   turno, (a) linha neste contrato e (b) arquivo em `~/.claude/projects/-opt-wiki/memory/`
>   com o gatilho de recall. Documentar depois é não documentar.

### Texto do item 14

> **Opus 5 executa, `advisor` aconselha, Fable 5.1 refuta o que é caro, Sonnet não entra
> (ordem do dono, 2026-09-15).** A DEC-019 e o §10 mantêm que nenhum modelo é superior por
> identidade e que divergência técnica se resolve por evidência. O que esta ordem fixa é
> **alocação de custo e de capacidade**, não hierarquia:
>
> - **Opus 5 é o default de execução e de orquestração**, em toda frente e todo subagente de
>   trabalho. Onde o harness escolheria outro modelo, declara-se `model: 'opus'`.
> - **O `advisor` é obrigatório**, para a sessão principal e **para cada agente lançado**. Ele
>   recebe o transcript inteiro, **é o próprio Fable 5.1 e custa menos que lançá-lo**. Cadência
>   mínima: antes de cada frente, ao mudar de abordagem, quando a medição contraria o
>   esperado, e antes de declarar pronto — com o entregável já durável no disco.
> - **Fable 5.1 direto (`Agent` com `model: 'fable'`) é para momento crítico**, e o prompt
>   pede **REFUTAÇÃO com evidência**, nunca "o que você acha?". Usa-se antes de algo caro de
>   reverter. **Consultar o `advisor` primeiro** — Fable lançado onde o advisor bastaria é
>   desperdício.
> - **Sonnet não entra neste projeto**, em nenhuma etapa. O parágrafo anterior desta política,
>   que previa "Sonnet 5 leve", fica **superado nesta data**, com o motivo: o projeto exige
>   raciocínio sobre contrato, medição e código simultaneamente, e erro barato de modelo custa
>   caro de retrabalho.
> - **Concordância entre agentes não é verificação; refutação tentada e falhada é** — e isso
>   não muda.
>
> **Superado em 2026-09-22 (ordem do dono):** Fable 5.1 orquestra toda sessão e refuta, Opus 5.5
> é o padrão de execução, Sonnet 5 volta ao projeto só para colher contexto (escrita apenas em
> `.agents/runtime/contexto/`) e Haiku é proibido. O texto acima fica como foi decidido; o que
> vale está em `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` §3 e na DEC-060.

### Texto do item 13

> **REESCRITO EM 2026-09-16 contra fonte primária.** A versão anterior deste bloco dizia *"o
> Provimento 205/2021 e os **arts. 42 a 47** do CED"* e formulava a regra em **dois** regimes.
> As duas coisas estão erradas: o intervalo omite justamente o **art. 39**, e a redação literal
> tem **três** regimes. O texto antigo não se apaga — fica aqui registrado como o que era —, e
> o que vale é o abaixo. Fundamento com URL, bytes e SHA-256 de cada dispositivo:
> **`docs/goal/JURIDICO_BASE.md`**, §1.1.

> **A ética da OAB tem TRÊS regimes, e o deste portal é o do meio (ordem do dono, 2026-09-15;
> precisão de 2026-09-16).**
>
> | regime | alcança | dispositivos conferidos |
> |---|---|---|
> | **A — publicidade profissional** | anúncio, oferta, perfil profissional, captação | CED arts. 39, 40, 44, 45, 46; Prov. 205/2021 arts. 3º, 5º, 6º |
> | **B — conteúdo informativo: PERMITIDO, com deveres de FORMA** | artigo, verbete, comentário de acórdão, dataset, resposta pública | CED art. 41 (não induzir a litigar), art. 42, I (não responder consulta de caso concreto em canal público), art. 42, IV, art. 43 (sem sensacionalismo); Prov. art. 4º e Anexo Único |
> | **C — fora da disciplina** | **exatidão técnica da informação jurídica** em conteúdo informativo | nenhum dispositivo a alcança. Os três que mais se aproximam — EAOAB art. 34, XIV; CED art. 2º p.ú. II e art. 6º — são **processuais e dolosos**, e não alcançam verbete |
>
> **O regime B é o deste portal, e é de permissão com forma — não de proibição.** Ignorar o
> regime B erra para um lado (publica o que o art. 42, I veda); tratar B como se fosse A erra
> para o outro (trava página informativa invocando norma de anúncio). **Os dois erros já
> aconteceram neste repositório**, e a versão anterior deste bloco cometia o segundo.
>
> - **O CTA de WhatsApp tem autorização EXPRESSA, por dispositivo.** O Prov. art. 4º, §3º
>   *equipara ao e-mail* *"todos os dados de contato e meios de comunicação… inclusive os
>   endereços dos sites, das redes sociais e os aplicativos de mensagens instantâneas"*, desde
>   que em caráter informativo. A letra fria do CED art. 40, V, lida isolada, diria o contrário
>   e travaria o portal. **"Tire suas dúvidas pelo WhatsApp" fica — não se remove.**
> - **Jurisprudência pública de terceiro FICA; caso do próprio advogado com resultado SAI**,
>   ainda que anonimizado (Prov. art. 4º, §2º, que veda resultado obtido *"em procedimentos que
>   patrocina ou participa"*). É o dispositivo que protege as ~875 páginas de
>   `/jurisprudencia/`.
> - **O que sai sempre:** imperativo de contratar ou litigar (Prov. art. 3º, §1º; CED art. 41);
>   promessa de resultado (Prov. art. 6º, p.ú.); preço, desconto e gratuidade como chamariz
>   (Prov. art. 3º, I) — **explicar gratuidade de justiça ou BPC/LOAS como instituto jurídico
>   não é isso**; especialidade sem título (Prov. art. 3º, III); sensacionalismo (CED art. 43).
>
> - **Onde o Provimento 205/2021 continua valendo, sem afrouxar nada:** CTA comercial, oferta
>   de serviço, preço, promessa de resultado, captação indevida, e a inscrição na OAB nas
>   peças de rede social (art. 44, §1º do CED). Esses gates ficam como estão.
> - **Proibido invocar "risco sob a OAB", "exposição disciplinar" ou "responsabilidade
>   profissional" como motivo para bloquear, adiar ou reduzir publicação de conteúdo
>   informativo.** Quem alegar risco disciplinar **cita o dispositivo** — provimento, artigo
>   do CED, ementa de julgado do TED. Sem dispositivo citado, a rota segue aberta.
> - **Erro de conteúdo é defeito de QUALIDADE, e se trata como tal:** conserta-se o produtor,
>   mede-se antes e depois, e a página **publica e refina** (§5). Erro de conteúdo **não é
>   infração disciplinar** e não justifica trava.
> - **Precedente que originou a regra:** nesta sessão classifiquei "citação legal mal
>   atribuída" como *"P1 permanente, a única classe com risco real sob a OAB"* e transformei
>   isso em pré-requisito bloqueante da escala. Era invenção: nenhuma norma da OAB trata de
>   precisão de citação em conteúdo informativo. O defeito é real (15,51% dos itens do modelo
>   não provam o artigo no trecho) e **se conserta**; o enquadramento disciplinar era falso e
>   **cai**.

### Texto do item 8

> **Nenhuma decisão volta para o dono; nenhuma revisão de conteúdo é dele (ordem de
> 2026-09-15).** O acervo tem dezenas de milhares de páginas e cresce sozinho: auditoria
> página a página por pessoa é impossível por construção, e desenhar a esteira supondo essa
> auditoria é desenhar uma esteira que não anda. **Quem decide é o Claude Code; quem julga
> conteúdo em escala é o cérebro**, pelo contexto e com medição gravada, nos limites do §5.
>
> - **Proibido devolver decisão técnica**, inclusive como "registrar como DEC e aguardar",
>   "confirmar antes de prosseguir" ou "opção (a) ou (b)".
> - **Proibido desenhar "revisão humana" como etapa de esteira** de conteúdo. Onde se
>   escreveria "um revisor lê e decide", escreve-se o critério medível que o cérebro aplica,
>   mais a amostra de controle de falso positivo **e** falso negativo.
> - **Proibido travar frente por falta de aprovação.** Ambiguidade se resolve pela rota mais
>   conservadora **que ainda entrega**, com a suposição escrita no commit.
> - O limite continua sendo o do contrato de máquina: não destruir trabalho, não quebrar
>   produção, não fraudar. Esses não são decisão — são proibição.

### Texto do item 9

> **Dado público se usa até o fim da cadeia, inclusive em página publicada (ordem do dono,
> 2026-09-15).** O §2 já diz que API pública brasileira é livre para usar, consultar,
> armazenar, indexar e **servir**. Fica explícito o que faltava: **isso alcança o artefato
> público**, não para em "sinal interno". **DataJud, API Pública do CNJ, DJEN, LexML,
> `normas.leg.br`, Planalto, diários oficiais e portais da transparência entram no caminho
> de publicação.**
>
> - **Proibido criar — ou manter — trava de import, gate, allowlist ou regra de "só sinal
>   interno" apoiada em:** cláusula de termo de uso de API pública; receio jurídico sem norma
>   citada; ou **defasagem do dado**. Defasagem conhecida se **declara** na proveniência.
> - **A linha que fica é a que a lei nomeia:** segredo de justiça (`nivelSigilo > 0`,
>   marcado na própria API), ECA, Maria da Penha, adoção e dado sensível do art. 5º, II da
>   LGPD. Sai IDENTIFICADOR (CPF, RG); **nome de parte e de agente público em ato oficial
>   publicado PODE constar**.
> - **O DataJud é o caso nominal, e está DESTRAVADO.** O dono ordena isso repetidamente e
>   sessões sucessivas voltam a travá-lo — porque a regra não estava escrita. **Fica escrita
>   agora, e não se reabre.** Entra: processo individual, número, classe, órgão, relator,
>   andamento e **nome das partes** (CPC art. 189: *"os atos processuais são públicos"*).
> - **Proibido em qualquer sessão futura:** reabrir esta decisão; reintroduzir trava contra
>   fonte pública; ou estreitar o escopo para "agregado apenas", "sinal interno apenas" ou
>   "sem nome de parte". Quem achar que há risco novo **cita a norma e o dispositivo**. Sem
>   norma citada, a rota segue aberta.

### Item de manutenção que o próprio contrato pede

`CLAUDE.md:128` declara **"11.039 páginas públicas (medido em 2026-09-09)"**. Medi hoje
**11.106**. O parágrafo manda atualizar a linha junto com o número, e
`check-contrato-vs-medicao` tem tolerância de `max(200, 5%)` — **não reprova hoje**, e por
isso a divergência passa despercebida.

---

# 2.9 MODO DE OPERAÇÃO — o runbook, e o que ele descobriu

Workflow de 17 agentes: 5 varreduras operacionais, 5 runbooks por bloco, 5 refutações, crítico e
síntese. Registro durável em `~/.claude/plans/pure-imagining-cerf-agent-a05f17d991413d4d7.md`
(2.283 linhas, 18 seções). Medição própria do sintetizador, independente dos runbooks: onde os
dois conjuntos coincidem, o número está marcado `[M×2]`.

## 2.9.1 Dois defeitos VIVOS que nenhuma investigação anterior pegou

**A1 — `wikijuridica-server-reload.path` reinicia o Go SEM GUARDA, e já quase mordeu.** Disparou
**3× em 24 h**, e a de **12:29:55 caiu 58 segundos depois** do publish da onda. **Não há
condição**: ele reinicia porque um arquivo mudou, no meio do que estiver acontecendo.
**MEDIDO DE NOVO EM 2026-09-16, e a correção mudou.** A unit observa **três** arquivos
(`data/ai/embeddings/ativo.json`, `data/ai/grafo_vizinhanca.jsonl`, `data/ai/risco_superacao.jsonl`)
e aciona `systemctl restart wikijuridica-server.service` **como root, sem nenhuma condição**. Nas
últimas 24 h houve **2 disparos**, e o quase-acidente se repetiu: o de **04:52:02** caiu **108
segundos** depois do fim da onda diária (04:50:14).

**O desastre concreto já está escrito no repositório**, em
`ops/systemd/wikijuridica-daily-content.service:36-43`: um restart entre a escrita do sitemap e a
do manifesto deixa o disco com *sitemap sem manifesto*, o que **aborta o boot** do servidor
(`publishedmanifest.Validate`); com `Restart=always`, `RestartSec=5` e `StartLimitIntervalSec=0`,
o resultado é **laço infinito de reinício**.

⇒ **A correção NÃO é `ConditionPathExists`, e também não é o `stop` procedural que eu havia
escrito.** `PathChanged` é *edge-triggered*: condição falsa ⇒ a unit é **pulada** ⇒ **o restart se
perde para sempre**, o servidor fica com índice velho e `buscar_semantico` some de `tools/list` —
exatamente o que a unit existe para evitar. A guarda tem de **esperar**, não pular.

**O wrapper `tools/aguardar-fim-de-deploy`** espera o lock de transação
(`data/ops/.deploy-em-curso.lock`, que `tools/deploy-publico:196-203` re-toca a cada 30 s) e só
então executa o `restart`. Janela de órfão: **1800 s**, a mesma constante que
`check-portal-health:431-437`, `check-producao-saudavel:55-67` e `deploy-binario-go:628` já usam.
Teto de espera 2400 s ⇒ `exit 2` ⇒ o `OnFailure` que a unit **já declara** dispara de verdade
(não há `SuccessExitStatus` ali).

**Isto substitui a linha de runbook que eu havia escrito** (*"o `stop` dessa unit é pré-condição
de toda transação"*): guarda procedural depende de um operador lembrar dela em cinco runbooks; o
wrapper não esquece, e não perde o restart.

> **EXECUTADO EM 2026-09-16 — e o wrapper existe: `tools/aguardar-fim-de-deploy`.**
> `wikijuridica-server-reload.service` passou a chamá-lo, com `TimeoutStartSec=2700`
> (> o teto de espera de 2.400 s). Duas correções ao que estava escrito acima:
>
> - **O lock tem CINCO leitores, não quatro.** O quinto é Go —
>   `internal/checks/http_smoke_redesocial.go:60,66` — e ele escreve a janela em **minutos**
>   (`30 * time.Minute`). A constante passou a morar em `tools/lib/deploy_lock.env`; os cinco
>   leitores **continuam com o literal de propósito** (reescrever produção que funciona,
>   inclusive Go no caminho de serving, é a regressão que o contrato proíbe), e quem impede a
>   deriva é `tools/test_aguardar_fim_de_deploy.sh`, que fixa os literais contra o env e
>   verifica a **equivalência** de unidade em vez de exigir segundos do Go.
> - **NADA NA ONDA DIÁRIA CRIA O LOCK.** `grep -rn deploy-em-curso` devolve apenas
>   `tools/deploy-publico:127` e `tools/deploy-binario-go:628` como criadores —
>   `tools/run-daily-content` **não toca o lock**. Ou seja: o wrapper protege a transação do
>   **deploy**, mas **não** protegeria o incidente de 04:52:02 citado logo acima, porque
>   naquela janela não havia lock nenhum no disco. **Fechar essa metade é trabalho seguinte**
>   (tocar o lock em volta das etapas 8/9 de `run-daily-content`, que é bash e está no
>   escopo), e fica escrito aqui para que ninguém leia o wrapper como cobertura completa.
>
> A espera é por **FIFO aberto em `<>` e desligado do filesystem** — sem `sleep` (barrado por
> hook), sem busy-wait e sem processo auxiliar. A primeira versão usava
> `exec {fd}< <(exec cat)` e **travava sob captura de saída**, porque o `cat` herda o stderr
> capturado e nunca o fecha.

**A3 — o canal de máquina está mentindo o hash, agora.** `/api/v1/citar` declara
`markdown_sha256` que **não bate com a gêmea servida pela borda: 13 de 13 divergem.** É a
superfície que um agente de IA usa para **citar com segurança**, e ela está errada em 100% da
amostra.

**A2 — 67 páginas anunciam tema 404 neste momento**, e não é teórico: **Amazonbot 7 e GPTBot 2 já
bateram no vazio** no log vivo.

## 2.9.2 A descoberta que barateia a verificação

**O `ETag` da gêmea Markdown É o `sha256[:32]`** — conferido na origem e na borda. Logo **a
paridade do canal de máquina se verifica por `HEAD`, sem baixar corpo**: amostra de 100+ em vez
de 6. O predicado foi validado antes de existir, contra uma amostra por stride disjunta:
**pegou 10 de 10 divergências.**

## 2.9.3 Três correções que mudam o que se executa

| corrigido | de | para |
|---|---|---|
| teto do contrato / ganho de páginas | 555 ou 488 | **11.621 / 11.691 — ganho de 70** |
| units que tomam o flock pesado | 3 | **6** (faltavam `noticias-coleta`, 4×/dia, e `official-source-url-inventory-refresh`) — a `qualidade-longa` das 02:11 **engoliria o `flock -w 600`** que um runbook prescrevia |
| units que mascaram exit ≠ 0 | 9 | **10** (faltava `wikijuridica-bot-telemetry`) |

**E publicar NÃO renova a carência do sitemap** — lido no código: remove apenas
`carencia_vencida`. Vira **restrição datada**, com janela `07:50Z → 15:20Z`.

## 2.9.4 Os cinco runbooks prescreviam um comando PROIBIDO

Todos os cinco mandavam **esvaziar o índice do git** antes de passar a vez — e
`~/.claude/hooks/git-guard.sh:64-75,119` **barra** `git reset`, `git restore`, `git checkout --`,
`clean`, `revert` e `stash`. A condição é alcançável em todos os blocos: commit reprovado deixa
`.go` no índice.

**A saída sancionada, que vira linha do runbook:**
`git commit -F <msg> -- <caminhos exatos>` **commita da worktree sem passar pelo índice**
(`~/.claude/CLAUDE.md:102`). Índice sujo se resolve **corrigindo a causa e recommitando** —
nunca descartando.

## 2.9.5 A cadeia dos "31 dias" NÃO se aplica — e isso precisa ficar escrito

`docs/CADEIA_EDITORIAL_ORDEM_DE_REGENERACAO.md:25-80`: os 13 elos são `authorial_mass_*`, e os 5
detectores `older_than` **não leem `v2_pages`**. **Nenhum bloco deste plano precisa dos 13
passos.** Escrever isso é trabalho: ver `fingerprint mismatch` e "regenerar a cadeia" **é o erro
que custou os 31 dias**. Para `v2_pages` a rota certa é `ops/relaunch-writing.sh`.

> **Vermelho latente que ninguém tinha visto:** `authorial_mass_drafts.jsonl` tem mtime
> **2026-09-10 23:41** contra `authorial_mass_publication_readiness.jsonl` de **2026-08-05
> 19:38** — **saída 36 dias mais velha que a entrada**, que é a forma exata que
> `internal/authorialmassreadiness/readiness.go:1060` emite. E o `drafts` está ` M`.
> **Datar como baseline antes do primeiro commit**, senão este plano herda a culpa de um defeito
> que não causou.

## 2.9.6 O passo 2.6 falta nos dois blocos que publicam

`tools/deploy-publico:678` — o comentário em `:652-684` é explícito: o índice de co-citação *"tem
de nascer DEPOIS da republicação e ANTES de o serviço voltar a atender"*. Medido: índice em
**2026-09-11 03:08:12** contra `content/pages.json` em **2026-09-15 12:28:56** — **4 dias atrás
da fonte**.

**E é invisível:** `./tools/check-percursos-fundamento-legal` sai **EXIT=0** com
`paginas=5815 links=31102 (78,1% cross-area)`. **Ele mede densidade, não frescor.** O P1b também
reescreve `pages.json` e reinicia — então precisa do 2.6 tanto quanto o P6.

## 2.9.7 Sobre a atestação do grafo — fechada, com uma exceção

`go-modern list -deps` = **98 pacotes**. **FORA** do grafo: `cerebro`, `ollama`, `checks`,
`stjacordaos`, `codex2policyenforcement`, `datajudfila`, `v2bodyneardup`, `tetodelote` — ou seja,
**quase tudo que o plano toca**. **DENTRO**: `quality`, `legalsignature`, `seo`,
`publishedmanifest` e **`ptbrtext`**.

**A exceção que quase passou:** a tabela de gates proíbe mexer em `quality` e `legalsignature` e
**esquece `internal/ptbrtext`** — que está no grafo **e** é chamado em
`cmd/generate-acordao-pages/main.go:859`, exatamente onde o "SE NÃO VIER" de um passo manda
mexer.

*E o pareamento contra o commit PAI está coberto por um hook que nenhum runbook citava:
`check-v2-finalized-commit` não está no `pre-commit` — quem o invoca é
`.githooks/reference-transaction:240-248`, lendo o checker **do `$BASE`**. É fail-closed em
`update-ref`, `--no-verify` não contorna, e **a recusa não aparece no log do pre-commit**, que é
onde o runbook mandava olhar.*

## 2.9.8 Nota de honestidade do próprio workflow

O crítico de completude registrou: **o `advisor` estava rate-limited**. Ele declarou em vez de
omitir, e no lugar fez **autorrefutação dirigida** contra os seus dois achados mais caros — os
dois **sobreviveram e ficaram mais fortes**. Os oito conflitos entre runbooks foram decididos em
§0 com o critério explícito, e **não se re-litigam nos passos**. As 16 regras de parada foram
escritas **antes** dos números, e reverter é sempre para frente.

---

# 3. Verificação

```bash
# P1b — o dado corrompido parou de ser servido (a verificação mais urgente)
#   zero páginas com dateModified anterior a datePublished no HTML SERVIDO:
./tools/go-modern run ./cmd/check cronologia-de-publicacao     # gate novo do P1b
#   e o registro de estreia voltou a cobrir o manifesto (10.107 -> 11.106):
python3 -c "import json;print(len(json.load(open('data/editorial/first_published_at.json'))),'chaves')"

# P4 — a régua do produtor virou a régua do gate; o molde deve despencar de 1.405
./tools/go-modern test -count=1 ./internal/v2bodyneardup/
./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 5000

# P1 — a coleta voltou, com os 10 datasets
./tools/go-modern test -count=1 ./internal/stjacordaos/
systemctl start wikijuridica-stj-acordaos-coleta && systemctl status --no-pager
python3 -c "import json;print(len(json.load(open('data/corpus/jurisprudencia/stj-espelhos/cursor.json'))['datasets']))"

# P2 — as chaves voltaram a casar (nenhuma saída = correto)
bash -c 'source /dev/stdin <<<"$(sed -n "/^declare -A COLETORES/,/^)/p" tools/run-daily-content)"
  for k in "${!COLETORES[@]}"; do case "$k" in *" "*) echo "CHAVE COM ESPACO: $k";; esac; done'

# P3 — a família dos órfãos morreu
./tools/go-modern run ./cmd/check produtor-orfao
grep -rln tetodelote cmd/          # os dois motores do cérebro têm de aparecer

# P4 — o motor avança entre passadas (o teste do defeito confirmado)
./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 30   # 1ª
./tools/go-modern run ./cmd/generate-acordao-pages -seco -limite 30   # 2ª: intents DIFERENTES
./tools/check-v2-portfolio-pairing && ./tools/check-http-smoke

# P6/P10 — âncora e atribuição guardadas
./tools/go-modern test -count=1 ./internal/cerebro/
./tools/medir-ancoras-de-dispositivo
./tools/go-modern run ./cmd/check contrato-dado-real

# P8 — cérebro vivo e capacidade pública anunciada
systemctl status wikijuridica-cerebro ollama
curl -s -X POST 127.0.0.1:8089/mcp -d '{"method":"tools/list"}' | grep buscar_semantico
```

## Provas de aceitação

| passo | prova objetiva |
|---|---|
| P1 | cursor com **10 datasets**; elegibilidade do §1.3 refeita sobre o corpus completo |
| P1b | **zero** páginas com `dateModified < datePublished` em `public/`; `first_published_at.json` cobre 11.106 chaves; `publicado_em` deixa de vir vazio em `/api/v1`; prova negativa: forjar uma cronologia impossível ⇒ gate vermelho nomeando a rota |
| P2 | nenhuma chave com espaço; gate diário volta a julgar **hoje** (hoje cita `(2026-09-10)`); `--somente-noticias` volta a rodar coletas; `--seco` volta a existir (hoje `exit 2` em `:105`) |
| P4 | `molde_acima_do_limiar` cai de **1.405**; nenhum par do acervo acima de 0,70 pela régua real (máximo medido hoje: 0,5193); o regex de itens recupera **675 de 682 com 0 regressões** sobre os 4.079 que já funcionam |
| P3 | prova negativa: remover linha do registro ⇒ gate vermelho nomeando o arquivo |
| P6 | duas passadas `-seco -limite 30` devolvem conjuntos **disjuntos**; a prova de travessia leva o manifesto de 11.106 para cima com `manifest ⊆ sitemap ⊆ public` e SHA batendo; e o `-limite` abre em seguida, no mesmo turno |
| P5 | teste reescrito cobra `nivelSigilo` e proveniência; página de DataJud no ar com a data do dado visível |
| P6 | `artigo_no_texto_citado_pct` medido antes e depois, sobre a população inteira |
| P8 | prova negativa roteirizada: derrubar Ollama, remover modelo, `kill -9`, `kill -STOP`, corromper fila, segurar flock, forçar teto a 1 byte. **Nenhuma das sete produz tarefa nova em `erro`**; as curáveis voltam sozinhas; as não-curáveis alertam dentro do limiar |
| P10 | os 4 checks órfãos aparecem no ledger da bancada |
| P12 | tabela de tok/s preenchida com **medição**, estimativas aposentadas |

## Regras de parada, decididas antes do número

- Probe do P6 mostrar molde ou prosa repetida **medido pela régua do gate real** ⇒
  **corrige-se o gerador**, nunca se afrouxa o gate. A recíproca também vale e é o P4: recusa
  por régua que **não** é a do gate não é molde — é bug do produtor.
- P6 derrubar a taxa de promoção ⇒ **o número cai e está certo**.
- Âncora literal sair de **100,0000%** em qualquer passo ⇒ **para o pipeline de extração** e
  investiga: trecho não ancorado é invenção, e invenção é fato, não juízo. Não para a
  publicação do que já está ancorado.
- Atribuição piorar depois do P5 ⇒ **reverte a mudança do P5**, não a publicação. Atribuição
  é defeito de qualidade que se refina; não é trava.

---

# 4. Estado da verificação

Ordem do dono, 2026-09-15: *"Se não está verificado, lance agentes para verificar. Nada de
deixar para depois."* · *"Se tem lacunas, investigar. Eu pago."* · *"Cada dado achado de
agentes deve entrar no plano e ser investigado se vier truncado ou parcial. Enquanto não
tiver 100% dos dados suficientes para executar, não terá plano."*

## 4.1 Lacunas FECHADAS nesta sessão, por refutação adversarial

| # | Lacuna | Como fechou |
|---|---|---|
| 1 | Elegibilidade era replicação minha, não do Go | **FECHADA e REFUTADA.** Binário com `-seco`: 2.560 / 4.763 / **+2.203**. Meu número estava 5,3× inflado por omitir `procedimental()` em `main.go:515`. Dois agentes independentes reproduziram o erro **e** a correção. §1.3 |
| 2 | A âncora de 100% é tautológica | **FECHADA e QUANTIFICADA.** Confirmada a tautologia; medida a atribuição real: **15,51%** dos itens do modelo sem o artigo no trecho, **19,0%** apoiados na folga, **13,1%** sem nem artigo nem norma, **1.966** itens descartados por invenção. **173 páginas** destravadas com atribuição não provada. §1.4 |
| 3 | Os 6 datasets ausentes existem upstream? | **FECHADA.** WebFetch com UA canônico: quinta-turma 48 recursos, corte-especial 44, primeira-seção 51, terceira-seção 51, segunda-turma 62, sexta-turma 48. Todos CC-BY, último `20260831.json`. §1.1 |
| 4 | A falha é malformação do upstream ou truncamento nosso? | **FECHADA.** `cliente.go:190-196` lê `limite+1` e erra explicitamente — nunca trunca em silêncio. Ensaio direto reproduziu `invalid character '}' after array element` em 31 s. §1.1 |
| 5 | Os 6 nunca foram coletados, ou foram e sumiram? | **FECHADA.** `cursor.json` nos 5 commits da história nunca teve mais de 4 datasets; `manifest.jsonl` só tem 4. §1.1 |
| 6 | O flock do cérebro está mesmo morto? | **FECHADA.** `systemctl show`: `PrivateTmp=yes`, `BindPaths=` vazio. Namespaces 4026532461 × 4026531841. Lock do daemon criado no minuto do `ExecStart`. Nenhum outro caminho de lock no código. §1.8 |
| 7 | O gate diário fica vazio ou congelado pela corrupção do shfmt? | **FECHADA e CORRIGIDA.** Não fica vazio: fica **congelado em 2026-09-10**. Hoje ele imprime `jurisprudencia OK` citando uma linha de 09-10 — **falha nova amanhã passaria verde**. Stale é pior que vazio: é cegueira com confiança. §1.7 |
| 8 | A régua do gerador diverge da do gate? | **FECHADA.** 3-gramas com dígito neutralizado × 5-gramas com dígito preservado, mesmo limiar 0,70. §1.17 |

## 4.2 Lacunas EM INVESTIGAÇÃO agora, nesta sessão

Quatro agentes Opus e um workflow de arquitetura rodando. Nenhuma fica para outra sessão.

| # | Lacuna | Quem fecha | O que tem de voltar |
|---|---|---|---|
| 9 | **Volume real do corpus pós-recuperação** (hoje: extrapolação de 9 meses, ±30%) | agente de volumes | bytes declarados pelo CKAN por recurso, razão acórdãos/MiB **por tipo de órgão** medida sobre o que já está no disco, banda derivada da dispersão medida |
| 10 | **`size_vram` existe no Ollama 0.33.3?** | agente de GPU | `strings` no binário, JSON cru de `/api/ps`, ou doc oficial da versão exata |
| 11 | **Teto de residentes a re-derivar para a GPU** | agente de GPU | o valor correto e o critério que substitui a soma (hipótese: pausar quando `size_vram < size`) |
| 12 | **k empírico da RTX 5060 Ti** (hoje: derivado de outra placa) | agente de GPU | tok/s medidos por terceiros em llama.cpp/Ollama, Q4, 4B/8B/14B/30B-A3B, com fonte |
| 13 | **Driver e CUDA para Blackwell sm_120** | agente de GPU | versão mínima; se o Ollama 0.33.3 embarca binário sm_120 ou cai em JIT |
| ~~14~~ | ~~`BindReadOnlyPaths` × `PrivateTmp=true`~~ | **FECHADA** | Rota preserva o isolamento. Fonte primária `namespace.c` do pacote exato; 3 condições de ordem escritas no §P9 |
| ~~15~~ | ~~Desde quando a coleta falha~~ | **FECHADA** | **7 falhas / 7 disparos**, 09-09 a 09-15, por `owner_alerts.jsonl`. Último sucesso 2026-09-10T07:32:07Z. Minha premissa de datar por commit era falsa — a unit grava o cursor a cada lote |
| ~~16~~ | ~~O limiter impede o `OnFailure`?~~ | **CONFIRMADA e pior** | Os `10s`/`5` são **defaults do manager**, não declarados — invisíveis ao grep. `check-units-alarme:84-106` já mediu: restart em laço **não** dispara (87 restarts em produção, sem alerta) |
| 24 | **Os 7 defeitos de robustez da onda diária**, que o publicador do P6 herdaria verbatim | agente da onda | veredito por defeito com arquivo:linha; em especial `first_published_at` corrompendo 999 páginas **por dia** e a fila de refino parada |
| ~~25~~ | ~~Pisos e regex que matam conteúdo~~ | **FECHADA — três gates burros confirmados, um refutado** | Piso: cortes de saída dispararam **0 vezes** em 4.763; líquido **~1.500–1.600**. Regex: mede a **quebra de linha do coletor** (74,3% de recusa em `2025-11`, **0,0%** em `2026-07`), **25 de 25 amostradas legítimas**; regra substituta recupera 675 de 682 **como fallback** (isolada quebraria 29). Agravos: catálogo nunca aplicado — mas **83,8% têm óbice real**, e o resíduo de mérito é de **poucas centenas**, não 1.388. Fila: **minha alegação refutada** — ela é regenerada a cada ingest, e o defeito é não haver **quem reescreva** |
| ~~17~~ | ~~Rendimento real sobre o poço~~ | **FECHADA — e REVERTIDA** | Passada exaustiva: **4.763 → 2.488 páginas**. 39,7% era **piso**, não teto: 39,7% → 42,3% → **52,2%**; por segmento **39,7% → 45,2% → 62,1%** |
| ~~18~~ | ~~Quantas recusas de molde o gate real aprovaria~~ | **FECHADA** | **135 de 135 aprovadas** pela régua real (a 0,70 e a 0,82); inverso **0**. Régua do gerador **estritamente dominada**. Máximo da família sob a régua real: **0,5193** — o limiar nunca mordeu |
| ~~19~~ | ~~Qual camada domina o score~~ | **FECHADA** | headings p50 = **1,0000**; FAQ 0,6867; **camada autoral 0,2469, com 1 par de 642.411** acima de 0,70 |
| ~~20~~ | ~~36 cortadas: laço ou ementa densa?~~ | **FECHADA — (b) ementa densa** | dose-resposta monótona (0% abaixo de 1k chars, 5,56% acima de 5k); nenhuma das 5.930 exibe assinatura de laço. Correção: **partir por item numerado**; 7 das 36 exigem corte por parágrafo |
| ~~24~~ | ~~Os 7 defeitos da onda diária~~ | **FECHADA — 7 verificados, 9 novos achados** | `first_published_at` promovido ao passo 1 do roteiro (§1.18); `SuccessExitStatus` mascarando exit 1 em **20 units**; `--seco` morto desde 09-09; duas filas de refino sem consumidor |
| 21 | **A família inteira de gates que recusa por juízo** | workflow de arquitetura | mapa com arquivo:linha, classe FATO/JUÍZO, régua e impacto medido |
| 22 | **Existe rota para os 49.807 agravos e embargos?** | workflow de arquitetura | agregação por tese, dispositivo ou relator — ou o motivo escrito de não haver |
| 23 | **O mecanismo de refutação de gate do §5 já foi usado?** | workflow de arquitetura | contagem histórica; e o incidente das "46 páginas, 46 falsos positivos" com o desfecho real |

## 4.2b Lacunas ABERTAS pelos próprios achados — nenhuma fica para outra sessão

| # | Lacuna | Como fecha |
|---|---|---|
| 26 | **CONFLITO: 805 × 1.225 × 2.477** para "dos 4.500, quantos têm âncora substantiva" (§1.20f) | Uma passada: contar com e sem `CarregaSobreposicao`, sobre **snapshot datado** do overlay, com o tokenizador do Go. A hipótese é que a divergência é exatamente a sobreposição do cérebro |
| 27 | **Quantas reprovações REAIS o piso de 12 palavras produziria** (§1.20b) | O medidor comparou o canal inteiro em vez do lote e não aplicou a isenção `maxLegalCitationSpanWords = 40`. Refazer com a semântica de `validate.go:21-22` e a isenção ligada |
| 28 | **A banda certa para página de acórdão** (§1.20a) | `verbete` (350–700) foi copiado; `guia_problema` (700–1400) existe. Medir o corpo montado das 2.488 sob as duas bandas e ver quantas das 144 recusas de orçamento sobrevivem |
| 29 | **`tetoCitado` 0,42 do produtor × 0,55 do gate** (§1.20a) | Rodar `-seco` com 0,55 e medir a variação em `citacao_abaixo_do_minimo_oficial` e `camada_autoral_nao_deixa_espaco` |
| 30 | **Volume real do corpus pós-recuperação** | Agente relançado com o parser já validado (21/21 por `content-disposition`) e a Corte Especial já medida em ~68 acórdãos/mês |
| 31 | **A síntese final da arquitetura de gates** | Workflow relançado com `resumeFromRunId`: os 12 agentes concluídos replicam do cache, roda só a síntese |

## 4.2c LACUNAS CRÍTICAS DE EXECUÇÃO — as que podem quebrar, não as de análise

Levantadas por mim como engenheiro responsável pela execução, **em investigação agora** por
red-team de 8 agentes. Elas não são dúvidas sobre o diagnóstico — o diagnóstico está fechado.
São as coisas que **quebram na hora de fazer**, e nenhuma foi exercitada.

| # | Lacuna | Por que me preocupa |
|---|---|---|
| 32 | **A travessia inédita** | `stj-acordao-derivado-01.jsonl` **nunca existiu**, nem no disco nem em HEAD. O P6 publica 2.488 páginas de uma **família nova**, e o gate de pareamento exige que o `intent_id` esteja no portfólio do **commit PAI** — o que cheira a ovo-e-galinha na primeira vez. **A resposta está no git**: qual foi a sequência exata de commits que criou `stj-tema-derivado-01`? |

> ### LACUNA 32 FECHADA EM 2026-09-16 — a receita existe, e foi usada DUAS vezes
>
> A pergunta era *"qual foi a sequência exata de commits que criou uma família
> inédita?"*, porque o gate de pareamento exige o `intent_id` no portfólio do commit
> **PAI** e isso cheirava a ovo-e-galinha. **Medido no git, e não há ovo-e-galinha:**
>
> | horário | commit | o que entrou |
> |---|---|---|
> | 12:04:42 | `376e4de4` | **portfólio** — 280 intenções |
> | 12:05:27 | `e9b354dd` | **páginas** — 280, 45 s depois |
> | 12:28:35 | `ceb2481a` | **portfólio** — 50 do STF |
> | 12:30:32 | `a62c27e1` | **páginas** — 50, 2 min depois |
>
> **Portfólio primeiro, páginas em commit SEPARADO logo em seguida** — exatamente o que
> o `CLAUDE.md` manda, e agora provado em duas famílias inéditas, no mesmo dia.
>
> **E o detalhe que teria custado uma tentativa:** o portfólio **não leva o nome do
> shard**. As páginas ficam em `v2_pages/stf-informativo-derivado-01.jsonl`, e o
> portfólio em `portfolio_v2/`**`jurisprudencia-stf-derivada-01.jsonl`** — nome por
> **área + tribunal**, não por família. Só há **3** portfólios de família derivada entre
> os 69 arquivos. Procurar o portfólio pelo nome do shard devolve vazio e faz parecer
> que ele não existe. *(Meu primeiro pareamento por nome concluiu exatamente isso, e
> estava errado — conferido: 60 páginas × 60 intenções, interseção 60/60.)*
>
> **A receita para o P6a, então:**
> 1. `data/editorial/portfolio_v2/jurisprudencia-stj-acordao-derivada-01.jsonl` → commit;
> 2. `data/editorial/v2_pages/stj-acordao-derivado-01.jsonl` → commit;
> 3. `./tools/check-v2-portfolio-pairing` **antes** de cada um — ele é read-only e evita
>    a tentativa cara (o pre-commit completo, com build Go de minutos).
| 33 | **O grafo de atestação** | Tocar `internal/v2ingest`, `go.mod` ou `go.sum` exige a atestação **no mesmo commit**, e **25+ testes reprovam depois de ~10 min de compilação**. O plano mexe em 7 pacotes e **ninguém verificou quais estão no grafo** — `go-modern list -deps` responde em uma linha |
| 34 | **A ordem topológica da cadeia editorial** | ~9 derivados, cada um obrigatoriamente mais novo que sua fonte; fora de ordem o erro diz `fingerprint mismatch` e **nunca** "ordem errada". **A fábrica já ficou 31 dias parada por isso.** O P6 publica **fora da onda** — em que posição do DAG ele entra? E `legal_cocitation_index.jsonl` só cabe no **passo 2.6 do deploy**: se o publicador não passa por lá, o que acontece com os "Percursos por fundamento legal" da gêmea? |
| 35 | **A escala de descoberta** | +2.488 páginas de uma vez é **+22% de acervo**. Sharding de sitemap, reordenação que muda URL de shard existente, 2.488 rotas nascendo **frias** na borda, e o aviso medido do contrato: publicação que zera `mtime` e `ETag` faz os bots **revalidarem e rebaixarem o acervo** — medido duas vezes com o `meta-externalagent` |
| 36 | **Concorrência e serialização** | O plano tem 14 frentes; a bancada diária segura o lock pesado **~70 min**; `run-heavy-throttled` **sai com código 75 em vez de esperar**; o pre-commit compila **o índice, não o pathspec** (77,6 s sujo contra 14,9 s limpo); e o cérebro escreve em `data/ai/` continuamente — o arquivo de extrações **cresceu 3× durante uma auditoria** |
| 37 | **A migração chegando no meio** | `fila.sqlite` tem 133 MB com **WAL vivo** e 3 tarefas em `executando`. O que acontece com elas se a máquina morrer? E o que **tem de ser medido antes de desligar a velha**, porque depois não dá para refazer: baseline pareado, piso de determinismo a temperatura 0, `sha256` do blob de cada modelo e `ollama --version` — **sem isso, "o mesmo modelo" nas duas máquinas é fé** |

**O red-team também tem ordem de descartar com evidência.** Lacuna que se revelar controlada
volta marcada como **CONTROLADO** com a prova do descarte — porque descartar errado é pior que
confirmar errado: ninguém volta a olhar.

## 4.3 Medição diferida e dívida herdada — o contrato de execução

Ordem do dono, 2026-09-15: *"Anotar o que não conseguiu medir nesta rodada, porque já medimos
muito e o plano tá começando a ter vida. O que não foi medido deve ser investigado na execução
do plano e implementado. E qualquer bug pré-existente é papel do Claude Code corrigir com
agentes, e não travar trabalho por bug anterior — até porque o projeto é um todo ligado, e
engenharia pura. Se uma peça estiver quebrada, o projeto pode quebrar."*

### 4.3.1 A regra das duas metades

Esta é a contraparte da Regra Zero, e as duas juntas fecham o ciclo:

| fase | o que vale |
|---|---|
| **planejamento** (agora) | lacuna se investiga **antes** de o plano ser submetido. Foi o que se fez: 37 itens, 21 fechados por medição |
| **execução** (depois da aprovação) | lacuna encontrada **no caminho** se mede **no caminho**, e o resultado entra no plano vivo — não vira nota para outra sessão |

O que muda entre as duas não é o rigor: é que na execução **há o sistema rodando para medir
contra**, e várias medições só existem depois de o primeiro artefato existir.

### 4.3.2 O que não deu para medir nesta rodada, e por quê

Nenhum destes é desculpa: cada um tem o **motivo estrutural** de não caber agora, e o **momento
exato** em que se mede.

| # | Não medido | Por que não cabia agora | Quando se mede |
|---|---|---|---|
| A | O rendimento real do gerador **depois** das três correções de régua | as correções não existem; `-seco` mede o código de hoje | primeira passada `-seco` após o P4, comparando recusa a recusa |
| B | Quantas das ~4.500 de ementa curta **sobrevivem à conferência de saída** | exige a constante trocada no binário | junto com A |
| C | O desempate 805 × 1.225 × 2.477 (§1.20f) | exige rodar com e sem `CarregaSobreposicao` sobre **snapshot datado** do overlay, que muda durante a medição | primeiro passo do P4 |
| D | Reprovações reais do piso de 12 palavras | o medidor comparou o canal inteiro em vez do lote e não aplicou a isenção de citação legal | ao ligar o detector no caminho de publicação |
| E | A banda certa para acórdão (`verbete` 350–700 × `guia_problema` 700–1400) | exige montar o corpo sob as duas bandas | junto com A |
| F | `tetoCitado` 0,42 do produtor × 0,55 do gate | idem | junto com A |
| G | Volume exato do corpus pós-recuperação e dos 460 MB de ZIP histórico | o censo `HEAD` da fonte respeita `Crawl-Delay: 10` — é teto do STJ, não nosso | durante o P1, com a coleta já rodando |
| H | Tudo o que depende da GPU: `size_vram` com placa, `k` real, se o `size` inclui KV | a placa não existe aqui | protocolo de dia um do P12 |
| I | `BindReadOnlyPaths` × `PrivateTmp` por inode | exige subir unit, que é mutação | primeira execução do P9 |
| J | Custo comparativo `CLAUDE.md` longo × skill + rules equivalente | a doc oficial **não cobre**, e o conjunto novo não existe | ao fim do P0a, medindo os dois |
| K | Campos do CSV de citação do Bing | só se conhecem na primeira execução autenticada | primeira coleta do P13 |
| L | Latência real publicar → citação, por agente | exige publicar e observar na borda | após a travessia do P6 |
| M | **Reconciliar 11.248 × 11.118 vetores semânticos** — dois instrumentos, duas contagens, nenhuma re-medida contra a outra | as duas vieram de passadas diferentes sobre um artefato que o cérebro reescreve; sem snapshot datado a comparação não se fecha (é a regra 12) | primeiro passo do P10, com `sha256` do `embeddings/ativo.json` anotado junto |
| N | **Re-derivar a tabela de tok/s do §P12 com o `k` medido na própria 5060 Ti** | a tabela ainda carrega valores da derivação anterior por banda: com `k = 0,65` e 448 GB/s o `qwen3.5:4b` (3,4 GB) dá **~86 tok/s**, não os ~79 impressos, e as linhas de 32B/70B misturam residente e offload sem declarar qual | dia um do P12, junto com o baseline pareado — **e a tabela nova sai de `medir_modelo` na placa, não de aritmética** |

**Regra de fechamento:** cada linha desta tabela é **passo do runbook**, não observação. Quem
executar a frente correspondente mede, grava com a camada declarada, e atualiza este plano. Item
que chegar ao fim da execução sem medição é **falha de execução**, não limitação do plano.

### 4.3.3 Dívida herdada: bug anterior não trava trabalho, e não se contorna

O princípio, e ele é de engenharia e não de disciplina: **o projeto é um sistema acoplado.** A
coleta alimenta o cérebro, que alimenta o gerador, que alimenta a publicação, que alimenta a
borda, que alimenta a citação. Peça quebrada no meio **não fica contida ali** — foi exatamente o
que esta investigação encontrou cinco vezes:

| a peça quebrada | o que ela derrubou adiante |
|---|---|
| um `}` sobrando num arquivo de 599 bytes do STJ | **6 de 10 datasets nunca coletados** — todo o criminal, todo o tributário, os uniformizadores |
| `shfmt` espaçando 8 chaves de array | o gate diário ficou **cego e congelado em 09-10**, e escondeu a fonte morta desde 08-29 |
| um produtor órfão sem runner | **944 páginas com data de estreia falsa**, servidas e re-datadas todo dia |
| régua divergente num produtor | **1.405 páginas** mortas, e o §5 do contrato tornado inexecutável por falta de ledger |
| `SuccessExitStatus=0 1` em 20 units | falha virou sucesso: `ExecMainStatus=1` **com** `Result=success` |

**O que isso obriga na execução:**

1. **Bug encontrado no caminho se conserta no caminho**, com agentes, na mesma sessão. Não se
   anota, não se contorna, não se usa como motivo para parar a frente.
2. **Não existe "isso já estava quebrado antes".** A pergunta certa é se a peça está no caminho
   do que se está fazendo — e num sistema acoplado, quase sempre está.
3. **Contornar é pior que consertar**, porque o contorno vira a próxima peça quebrada. A regra do
   contrato — *"suprimir o aviso em vez de resolver o que ele aponta é proibido"* — vale para
   defeito herdado igual.
4. **O limite continua sendo o mesmo, e é curto:** não destruir trabalho, não quebrar produção,
   não fraudar. Consertar dívida herdada não é autorização para reverter o que outra frente fez —
   o conserto é sempre **para frente** (`git reset`, `checkout`, `stash`, `clean` e `revert`
   seguem proibidos).
5. **Quando o conserto for grande**, ele vira frente própria no plano vivo com a medição que o
   justifica — mas a frente em curso **não para** por causa dele, salvo quando a peça quebrada é
   literalmente a que se está usando.

**Isto entra nos contratos como regra 20** (§P0c), porque é a que impede duas coisas opostas e
igualmente caras: parar o trabalho culpando o passado, e empilhar contorno sobre contorno.

## 4.3.4 LACUNAS CRÍTICAS DE EXECUÇÃO — resultado do red-team

Oito agentes, seis lacunas, refutação adversarial e re-verificação contra o disco em HEAD
`62d71de0` com o índice do git vazio. **Convenção de procedência aplicada a cada número: `[M]`
medido nesta sessão, `[H]` herdado de dossiê e não re-medido.** Um `[H]` nunca virou `[M]` por
concordância entre dossiês — e **dois `[H]` caíram na revisão**. Registro durável em
`~/.claude/plans/pure-imagining-cerf-agent-a560ab5b30c7c0dbc.md` (1.380 linhas).

### Os três BLOQUEANTES

**L1 — o teto de churn conta rota nova como re-datação.** `deploy-publico` sai com **exit 1
depois** de já ter publicado, purgado, aquecido e anunciado ao IndexNow — e o laço **se repete
em todo deploy seguinte**. Publicar 2.488 rotas novas dispara exatamente isso.

**L2 — `lane = "informativa"` desliga três instrumentos, e consertar depois é caro.** Arrumar
após a publicação é mudança de **atributo servido sem mudança de texto** ⇒ pela matriz do §6,
obriga `--ressemear` sobre **2.488 rotas**, re-data o acervo e re-anuncia tudo ao Googlebot.
**Tem de estar certo antes da primeira gravação.**

**L3 — `public/` está fora do backup por decisão escrita.** E o efeito não é só perder o acervo
estático: **derruba o boot do Go**. Com o nginx servindo `root public/`, é **queda total no dia
um** da migração.

### A decisão que o red-team tomou sem devolver ao dono

`cmd/generate-acordao-pages/main.go:76-78` declara `pageType = "verbete"` e
`lane = "informativa"`. Medido: **`generate-acordao-pages` é hoje o único gerador derivado com
valores que o `v2ingest` aceita** — os cinco irmãos usam `page_type` fora de `wordCountBands` e
lane `derivada_de_fonte_oficial`, que não está em `validLanes`. No último run do ingest, essa
lane teve **0 aceitos e 1.335 rejeitados**.

**Decisão: trocar os dois, para `"julgado"`** — que é o que a irmã que publica decisão judicial
(`stf-informativo-derivado-01`) já usa para o mesmo objeto. **Conferido no mapa canônico antes de
decidir** (`internal/content/content.go:310-331`): `"julgado"` existe e traduz para
`"jurisprudencia"`, então `CanonicalPageType` devolve `ok=true` e **não** cai no default
`"artigo"`. **Preço conhecido e aceito:** o pool reprovado pelo ingest sobe de 1.335 para 3.823
(+186%) — e o ingest **não está no caminho da publicação** (`v2publish.go:179` lê
`data/editorial/v2_pages/*.jsonl` direto).

### Os GRAVES, com o número que os sustenta

| # | o que é | medida |
|---|---|---|
| **L5** | a Cadeia B (publicação v2) não está declarada, e três passos faltam na onda | **67 de 67 rotas novas** sem co-citação e sem tema social; **88 respostas 404 de bot em 4 dias** |
| **L6** | a onda faz `git add` **por diretório** nos dois diretórios em que o P6 escreve, e publica | shard deixado na worktree ao atravessar 04:20±15 min ou 12:20 é **commitado sob mensagem de onda e publicado sem decisão** |
| **L7** | ponto cego do `strictjson` na guarda de commit | commit que toque só `internal/strictjson/*_test.go` **passa verde** e deixa a atestação stale ⇒ `ingest-v2-stock` recusa publicar e **nenhum deploy passa** |
| **L8** | nenhuma fase commitava os derivados da transação | `published_manifest.jsonl` **M há 5 dias** — e é dele que o gerador de estreia do P1b deriva a data ⇒ **o P1b nunca sai do lugar** |
| **L9** | o canal STJ não carrega `nivelSigilo` e não há filtro de exceção taxativa | **10.414 de 10.414 (100,0%)** com `nivel_sigilo` nulo; **8 casam Maria da Penha** e não há recusa nomeada |
| **L10** | gerador órfão com `-limite` default 30 | se o runner entrar **antes** da geração, a onda **estreia a família com 200 páginas em vez das 2.488** |
| **L11** | o índice de co-citação não tem detector de frescor | `check-percursos-fundamento-legal` sai **exit 0** contra índice **4 dias e 5.291 rotas atrás** |

**L9 é o que mais me preocupa como guardião:** é a única lacuna com consequência **jurídica
real**, não operacional. Oito acórdãos casam Maria da Penha, o campo de sigilo é nulo em 100%
dos registros, e o canal não tem recusa nomeada. **Entra no P6 como guarda obrigatória antes da
primeira gravação** — não depois.

### Oito preocupações DESCARTADAS com evidência — para ninguém reabrir

| preocupação | por que cai |
|---|---|
| os 6 pacotes que o plano muda estão no grafo do `v2ingest`? | **0 de 6** `[M]`. A atestação não trava o plano |
| o ordinal posicional do sitemap desloca shards existentes? | o registry ancora o número na **coorte**, não na posição |
| **IndexNow tem teto de 1.000/dia?** | **`MAX_URLS=1000` é POR REQUISIÇÃO.** Medido: **19.669 URLs num único dia, 20 de 20 lotes aceitos**. *(Derruba a premissa que eu havia usado para desenhar cadência — e a Regra Zero-C já proibia esse tipo de teto inventado.)* |
| aquecer 2.488 rotas frias é gargalo? | **207 s a 12 r/s**; o orçamento usa 62,5% em qualquer escala |
| +22% de acervo dispara revalidação em massa dos bots? | acréscimo de rota **não re-data** as 11.118 existentes; 304 do Googlebot segue em 53–60% |
| ovo-e-galinha no pareamento portfólio × páginas? | `FINALIZED:33-34` só casa `v2_pages/` ⇒ o commit 1 **não aciona** `check_page_product` |
| a Cadeia A (a dos "31 dias parada") é tocada pelo P6? | acoplamento **zero**, medido |
| P4/P6 precisam de snapshot de `data/ai/`? | `grep` por `data/ai` no gerador = **0** |

**E duas retratações**, que valem tanto quanto os achados: o red-team derrubou o próprio veredito
de que *"a família não nasce no canal de máquina"* — `publish-v2-direct --allow-public-write`
**reinicia o servidor** (`main.go:2257-2264`), então a gêmea nasce viva; o que falta sem o deploy
é o **passo 2.6**, que já é a L5.

## 4.4 O que permanece declaradamente não verificado

Só entra nesta lista o que **não é verificável nesta máquina**, com o teste que o fecharia.

1. **Desempenho real da RTX 5060 Ti neste workload.** Só se fecha com a placa na mão. O
   protocolo de migração do §P12 existe para isso e pré-registra o baseline **antes** de a
   máquina velha ser desligada — feito depois, não há como comparar.
2. **Se a régua nova de molde deixa passar prosa repetida em escala de 10 mil páginas.** Só
   se mede publicando o lote-probe de 200 e medindo o acervo real. É o passo 0 do §P6, e a
   regra de parada está escrita antes do número.

---

# 5. PROMPT DE EXECUÇÃO — 3.970 caracteres, contados antes da entrega

Ordem do dono: *"elabore um prompt no final do plano… com até 4k de caracteres calculados antes
de me enviar no terminal para eu copiar e colocar. Um prompt em modo operacional e que estimula
o Claude Code e os agentes a trabalharem, sem preguiça de IA."*

**Contagem: 3.970 caracteres** (`wc -m`, medido antes da entrega, teto 4.000).

*O parágrafo MODELOS do prompt abaixo está superado em 2026-09-22 (ordem do dono): a alocação
vigente está em `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` §3. Quem reusar este prompt
troca aquele parágrafo; o texto fica como foi entregue.*

```text
GOAL — executar o plano do cérebro (IA local) do /opt/wiki, inteiro, nesta sessão.

PLANO: docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md. Gravá-lo e commitá-lo é a ação nº 1 (P−1).

MODELOS. Opus 5 é o padrão de execução e de orquestração. O `advisor` é obrigatório — para você e
para todo agente que lançar: antes de cada frente, ao mudar de abordagem, quando a medição
contraria o esperado, e antes de declarar pronto, com o entregável já durável no disco. Fable 5.1
só para refutar o que é caro de reverter. Sonnet não entra em etapa nenhuma. Não há teto de
agentes: ondas dirigidas, cada leva nascendo do resultado medido da anterior, paralelos só em
arquivos diferentes.

ORDEM: P−1 · P0a · P0c · P0d · P0b · P0 · P1b · P1 · P2 · P3 · P6(travessia) · P4 · P6(lote) ·
P7 · P5 · P8 · P9 · P10 · P13 · P11 · P12. P14 fica em rascunho.
P6 tem dois momentos e a ordem é bloqueante: travessia mínima com `lane` e `pageType` já
corrigidos para "julgado" (arrumar depois obriga `--ressemear` sobre 2.488 rotas e re-data o
acervo), depois P4, depois `-seco` de recenseio, só então o lote com `-limite` aberto.
P11 não destrava o canal social: entrega os quatro critérios medíveis e o teste por mutação.
P12 entrega docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md e o protocolo de dia um — baseline
pareado, piso de determinismo a temperatura 0, sha256 do blob de cada modelo e `ollama --version`
medidos ANTES de a máquina velha desligar. Depois não há como refazer.

O QUE ESTÁ SANGRANDO AGORA, para não redescobrir: 944 páginas servidas com datePublished de hoje
e 942 com cronologia impossível (P1b); a coleta do STJ falha em 7 de 7 disparos e 6 de 10
datasets nunca existiram (P1); 8 chaves corrompidas pelo shfmt cegam o gate diário (P2); 1.405
páginas morrem numa régua que a régua real aprova 135 de 135 (P4); 20 units mascaram exit 1
(P10); ContentSHA256 erra em 10.070 de 10.070 rotas (P13).

COMO TRABALHAR
- Lacuna é trabalho, não limite. "Não dá para medir" é proibido enquanto houver rota de
  engenharia: cria-se a sonda, o gate, o parser, o ledger.
- Nenhuma decisão volta para o dono, nem disfarçada de "confirmar antes" ou "opção (a) ou (b)".
  Nenhuma revisão de conteúdo é dele.
- É proibido limitar este projeto. Volume mede-se na BORDA (Cloudflare); origem é piso.
- Bug pré-existente no caminho se conserta no caminho, com agentes, na mesma sessão. Contornar é
  pior que consertar: o contorno vira a próxima peça quebrada.
- Medição sobre artefato do cérebro exige snapshot datado — ele escreve enquanto você mede.
- Replicação que bate com o esperado é motivo para desconfiar dela. O binário é a autoridade.
- Achado de agente é alegação até você conferir no disco. Concordância entre agentes não é
  verificação; refutação tentada e falhada é.
- Sem prazo em dias. Portão é prova medida: passou, o passo seguinte abre no mesmo turno.
- Correção nasce com teste provado por mutação: se apagar a regra não deixa o teste vermelho, o
  teste é decorativo e não vale o commit.

COMANDOS
- Go só por ./tools/go-modern; escopo ./internal/... ./cmd/..., nunca full-tree.
- cmd/check sempre com o nome do gate; sem argumento ele roda todos e derruba o host.
- `git add <caminho exato>` e `git commit -F <arquivo>` em comandos SEPARADOS. Proibido reset,
  restore, checkout --, revert, stash, clean: índice sujo se resolve recommitando.
- `stop` de wikijuridica-server-reload.path é pré-condição de TODA transação.
- Passo 2.6 do deploy-publico (índice de co-citação) é obrigatório em todo bloco que republica.

PROVAS: zero páginas com dateModified < datePublished em public/; cursor do STJ com 10 datasets;
molde_acima_do_limiar caindo de 1.405; duas passadas `-seco -limite 30` devolvendo conjuntos
disjuntos; manifesto subindo de 11.106 com manifest ⊆ sitemap ⊆ public e SHA batendo; âncora
literal em 100,0000%. Cada frente termina com commit na mesma sessão.

Não pare para perguntar. Não deixe frente pela metade. Não relate pronto sem a medição no disco.
```

---

# 6. SEÇÃO DE ENGENHARIA — critérios de aceite, dependências, contratos e políticas

Acrescentada na gravação do plano no repositório (P−1), por exigência do goal aprovado em
2026-09-16. O corpo acima é o plano **na literalidade**; esta seção é o que torna cada frente
executável e verificável sem voltar ao dono.

## 6.1 Contrato de execução

| item | regra |
|---|---|
| **fonte da verdade do progresso** | `docs/goal/ESTADO.md` — item, status, evidência, lacuna, decisão. Atualizado **a cada item**, nunca ao fim |
| **evidência** | comando + saída + exit code, ou `arquivo:linha` no disco. Relato de agente sem evidência **não fecha item** |
| **proibido** | marcar feito sem evidência · stub · gambiarra · teste pulado, enfraquecido ou apagado · hardcode para passar · lacuna ignorada por "fora do escopo" |
| **rota bloqueada** | outra rota ao mesmo resultado. Complexo se decompõe, não se adia |
| **irreversível** | commit ou cópia datada em `.agents/runtime/` **antes** |
| **modelos** | Opus 5 padrão; `advisor` obrigatório (para mim e para cada agente); Fable 5.1 só para refutar o que é caro de reverter; Sonnet fora. **Superado em 2026-09-22 (ordem do dono):** Fable 5.1 orquestra e refuta, Opus 5.5 executa, Sonnet 5 só colhe contexto, Haiku proibido — `docs/goal/PROMPT_OPERACIONAL_DO_DONO_20260922.md` §3 |

## 6.2 Dependências entre frentes — o que não pode inverter

```
P−1 ──> tudo (o plano tem de estar no git antes de qualquer mudança)
P0a ──> P0c ──> P0/P0d/P0b        (formato antes de conteúdo; o P0a manda no formato)
P1b ──> P6                         (a data de estreia tem de parar de mentir antes de +2.488 rotas)
P2  ──> P1                         (o gate diário tem de enxergar antes de a coleta voltar)
P3  ──> P1b, P6                    (registro de produtores é o que impede o órfão de renascer)
P6(travessia) ──> P4 ──> P6(lote)  (lane/pageType certos ANTES da 1ª gravação; régua certa antes do lote)
P1  ──> P8                         (o criminal e o tributário só existem depois da coleta)
P5  ‖  P6                          (atribuição roda EM PARALELO; não bloqueia publicação)
```

**Amarras que atravessam todas:** `systemctl stop wikijuridica-server-reload.path` é
pré-condição de **toda** transação (§2.9.1 A1) · o **passo 2.6** do `deploy-publico` (índice de
co-citação) é obrigatório em **todo** bloco que republica (§2.9.6) · commit de Go serializa em
`/tmp/opt-wiki-agent-heavy.lock`, commit de conteúdo não.

## 6.3 Critérios de aceite, por frente

| frente | fecha quando |
|---|---|
| **P−1** | `git log -1 -- docs/goal/CEREBRO_IA_LOCAL_PLANO_20260915.md` devolve commit; nenhum anexo `untracked`; censo fora de `/tmp` |
| **P0a** | `CLAUDE.md` ≤ 200 linhas com teste que cobra o teto; hooks/rules/skills no disco e **medidos disparando**; `tools/check-modo-operacional` verde |
| **P0c** | teste `regras_do_dono_test.go` vermelho ao apagar **qualquer** das regras 8, 9, 13, 15, 16, 18 e 20 de **qualquer** documento da tabela (prova por mutação) |
| **P0d** | as armadilhas por arquivo em `docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md`, os precedentes em `docs/PRECEDENTES_DAS_ORDENS.md`, as decisões em `MAESTRO_CODEX_LOG.md` — cada uma com o número medido |
| **P0b** | `MEMORY.md` < 24 KB e < 190 linhas com gate que reprova acima disso; as 4 memórias novas gravadas; `.claude/rules/` com `paths:` para as armadilhas por arquivo |
| **P0** | 21 regras no `CLAUDE.md` como veredito de uma linha; gatilhos do §2 ligados ao **ato** |
| **P1b** | **zero** páginas com `dateModified < datePublished` em `public/`; `first_published_at.json` cobre as 11.106 chaves; `publicado_em` deixa de vir vazio em `/api/v1`; gate novo vermelho ao forjar cronologia impossível |
| **P1** | cursor com **10 datasets**; teste com a fixture de 599 bytes reprovando ao restaurar o `return`; guarda de órgão × dataset com 4 fixtures; `quarentena.jsonl` existindo; ledger de execução da coleta |
| **P2** | nenhuma chave de array associativo com espaço; `check-frescor-canal-diario` citando **hoje**; `--somente-noticias` coletando; `--seco` voltando a existir |
| **P3** | `ops/produtores-de-pagina.jsonl` existindo e sendo a fonte do mapa; gate `produtor-orfao` vermelho ao remover uma linha |
| **P4** | régua do produtor = `internal/v2bodyneardup` nos cinco eixos; `molde_acima_do_limiar` caindo de 1.405; regex de itens em **fallback** com 675 recuperados e **0 regressões** sobre os 4.079; ledger `intent_id` por recusa |
| **P6** | duas passadas `-seco -limite 30` devolvendo conjuntos **disjuntos**; travessia com `manifest ⊆ sitemap ⊆ public` e SHA batendo; `lane`/`pageType` = `julgado` desde a 1ª gravação; `nivelSigilo` e exceções taxativas filtradas antes de gravar |
| **P5** | `artigo_no_texto_citado_pct` medido antes e depois **sobre a população inteira**; catálogo de súmulas de fonte oficial com URL/data/hash; uma página entrando na fila de refino **e saindo dela refinada** |
| **P7** | os **dois** enforcers reescritos na mesma mudança; teste cobrando `nivelSigilo` + proveniência, com prova por mutação |
| **P8** | triagem por conteúdo aplicada aos barrados por classe, com taxa medida **por veículo** (`AREsp`, `AgRg no HC`, `AgInt`/`EDcl`); consumidor de `v2_rewrite_queue.jsonl` vivo |
| **P9** | as sete provas negativas do §3 roteirizadas e passando; `flock` com inode igual ao do host; `StartLimitIntervalSec` em `[Unit]`; `WatchdogSec` batido de dentro de `Roda` |
| **P10** | 4 checks órfãos no ledger da bancada; `SuccessExitStatus` removido das 20 units |
| **P13** | `data/ops/bing_webmaster_daily.jsonl` com bloco `citacao_ia_diaria`; gate `citacao-de-ia-nao-regride`; painel com a **camada declarada** em cada número |
| **P11** | os quatro critérios de destrava implementados com teste por mutação — **não** destrava o canal |
| **P12** | `docs/ops/IA_LOCAL_O_QUE_APROVEITAR_NA_GPU.md` com a tabela de tok/s **medida**, não estimada, e o protocolo de dia um gravado |

## 6.4 Políticas que valem em toda frente

1. **FATO é terminal; DIVERGÊNCIA é bug; JUÍZO nunca mata conteúdo** (§P4).
2. **Nenhuma decisão volta ao dono**; nenhuma revisão de conteúdo é dele.
3. **É proibido limitar o projeto** (Regra Zero-C). Volume mede-se na **borda**; origem é piso.
4. **Bug pré-existente no caminho se conserta no caminho** (regra 20), nunca se contorna.
5. **Toda área do Direito entra** (regra 1). Lacuna de área é pauta, não descarte.
6. **A ética da OAB alcança publicidade, não conteúdo informativo** (regra 13) — e o
   `docs/goal/JURIDICO_BASE.md` é a fonte primária anexada a todo briefing de conteúdo.
7. **Medição sobre artefato do cérebro exige snapshot datado** (regra 12).
8. **Correção nasce com teste provado por mutação.** Sem mutante morto, o teste é decorativo.
