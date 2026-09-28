# Rede social da Wiki Jurídica — implementação 100%, modo /goal

## Contexto

O `PLANO_REDE_SOCIAL.md` (2.407 linhas, aprovado em 2026-09-04) já fixou o desenho
jurídico e arquitetural. O que falta não é desenho — é execução, ordem e prova.

**Estado medido hoje (2026-09-05), por leitura do disco, não por comentário:**

| O que | Medido |
|---|---|
| Entregas do manifesto | **27 entregues / 75 pendentes** de 102 (`content/redesocial_entregas.json`) |
| O que o `cmd/social` (8091) serve | **1 página** de regras + gêmea `.md` + `/healthz` + `/readyz`. `/redesocial/feed` → 404 |
| Design | **Nenhum.** HTML nu, zero CSS — `cmd/social/render.go:20` documenta o porquê: a CSP só autoriza `/redesocial/assets/`, "que ainda não é servido por nenhuma location" |
| Motor pronto e **desligado** | `internal/contas` 4.746 linhas (Cadastrar, Entrar, OTP, CSRF, `AutorizaMudancaDeEstado`), `moderacao` 5.434, `lgpd` 3.680, `oabgate` 1.867, `djen` 2.708 — **nenhum com rota HTTP** |
| Domínio de conteúdo | **Não existe.** Zero tabelas de dúvida/resposta/thread/follow/perfil/tema |
| Bancos vivos | `var/social/social.db` (WAL) e `var/social/lgpd.db` — **`journal_mode=DELETE`, e é deliberado**: em WAL o efeito do `secure_delete` só se completa no checkpoint, e o art. 18, VI vale mais que concorrência de escrita (`lgpd/banco.go:60-72`, com teste que mede byte a byte) |
| Pacotes Go a criar | **17** · Gates a criar: **9** · Gates sociais hoje: 13 de **341** registrados em `checks.Names` |
| SMTP | `sendmail → msmtp` (cliente de relay, não MTA); `msmtpd` disabled, `postfix` masked, **nada escutando em 25/587/465** |
| Testes que já existem e passam | **437**, verdes, rodados agora: contas 91 · moderação 78 · guardião 54 · borda 51 · oabgate 47 · lgpd 47 · cmd/social 20 · resto 49 |

**Uma leitura que o número de entregas esconde:** 27 de 102 parece um começo, mas os
437 testes verdes dizem outra coisa — o que existe é **denso e provado**, não
esboçado. O trabalho não é consertar o que está lá; é construir a metade que falta e
ligá-la. Isso muda o risco da sessão: partimos de base limpa, e uma regressão nesses
437 é sinal imediato de que uma onda pisou onde não devia.

**O diagnóstico em uma frase:** é um motor de alta qualidade sem carroceria, sem
pintura e sem estrada. A engenharia de conformidade está feita; falta o produto.

**A ordem do dono nesta sessão:** 100%, nada parcial, nenhum dado descartado, design
premium dark — e o design **não está no manifesto**, então entra nele.

**O tamanho honesto do trabalho, depois do aditivo da §1 — e a contagem foi refeita
por script, não estimada.** Extraí todo ID citado neste dossiê e confrontei com o
manifesto: 121 IDs citados, dos quais **51 já existem** e **61 são novos** (os 9
restantes eram abreviação minha de IDs existentes — `F2-paginacao` por
`F2-paginacao-por-caminho`, e assim por diante; aditivo tem de usar o ID literal, ou
nasce entrega duplicada). Então **102 entregas viram 163**: 9 de design, 23 de produto
(§1.1-bis), 5 de decomposição do domínio, 2 de bots e o restante de carroceria e
lacunas de engenharia verificadas no disco.

**Duas** das pendentes já estão satisfeitas e só carregam prova errada ou rótulo velho
(§4) — `F05-dynamic-redirect-preserva-assets` e `F1-sqlite-import-allowlist` —, então
o estado do aditivo é **29 entregues, 2 suspensas com motivo e 132 a fazer**. Dessas
132, **10 não fecham por engenharia nenhuma** (§5): dependem de evento do mundo. Restam
**122 por engenharia**, e é esse o número que o goal cobra. Declarar pronto sem elas é
o que o gate `redesocial-entrega-final` existe para impedir.

O número cresceu 64% depois do refinamento, e isso é a informação, não o ruído: o
plano de ontem cobria conformidade e infraestrutura, e **não cobria produto**. Uma
rede social juridicamente impecável que ninguém usa é uma entrega falhada.

---

## 0-A. Modo `/goal` — a condição de encerramento, e ela não é negociável

Esta frente executa em **modo goal**. Goal não é uma sessão de trabalho: é um alvo com
condição de saída verificável, e **o goal não se conclui até tudo estar ok**.

**A condição de encerramento, literal:** `./tools/check-redesocial-entrega-final`
reprova **apenas** pelas dez entregas que dependem de evento do mundo (§5), cada uma
com a linha dizendo qual evento falta. Zero entregas pendentes por engenharia. Zero
entregas `suspenso` sem motivo escrito. Todos os gates citados por entrega `entregue`
executados e verdes.

O que **não** encerra o goal, e é preciso dizer para não haver dúvida: relatório de
progresso, plano atualizado, "as ondas 1 a 5 fecharam", teste passando localmente sem
o gate correspondente, ou entrega marcada `entregue` cuja prova eu não vi no disco.
Enquanto o gate terminal reprovar por engenharia, o goal **continua aberto** — e a
sessão seguinte retoma pelo prompt da §11, não do zero.

**Primeiro ato, antes de qualquer implementação:** este dossiê é copiado **na
literalidade** para `docs/goal/PLANO_EXECUCAO_REDE_SOCIAL.md` e **commitado**. Sem isso
o plano vive só em `~/.claude/plans/`, que não é caminho versionável e some — e um
plano que custou esta sessão inteira não pode depender de um diretório temporário.
Nenhuma linha de implementação antes desse commit.

### A tasklist operacional — derivada, nunca duplicada

O dono pediu tasklist operacional, e a decisão de engenharia é **não escrever uma
lista à mão**: `content/redesocial_entregas.json` já é a lista de tarefas, com 163
itens, estado, prova e fase. Uma segunda lista divergiria da primeira em uma semana —
é o mesmo defeito que fez a contagem fixa de linhas do `PRECEDENTES_DAS_ORDENS`
envelhecer e virar commit de correção.

Nasce então `tools/generate-social-tasklist`, que **deriva** a tasklist do manifesto e
escreve `docs/goal/TASKLIST_REDE_SOCIAL.md`. E ela segue o **padrão que este
repositório já tem** — `docs/goal/TASKLIST_PLANO_20260819.md`, cujo cabeçalho fixa a
regra que importa: *"Toda task tem TESTE — sem teste verificado, não vira `feito`"*.
Adotar o padrão existente vale mais que inventar um melhor.

| Coluna | De onde vem |
|---|---|
| `id` | o ID da entrega no manifesto |
| `task` | o título |
| `estado` | `pendente` · `fazendo` · `feito` · `bloqueado` |
| `teste` | a prova do manifesto, resolvida: o gate que fecha, o pacote, o arquivo |
| `onda` | campo novo `onda` no manifesto |

**A divisão entre os dois arquivos, que evita a divergência:** o manifesto guarda o
estado **durável e com prova** (`entregue`, `pendente`, `suspenso` — é o que o gate
cobra); a tasklist acrescenta os estados **efêmeros de execução** (`fazendo`,
`bloqueado`), que só fazem sentido enquanto a sessão corre e não pertencem a um
artefato versionado de contrato. Rodar de novo regenera; nunca se edita o `.md` à mão.
Assim o painel de execução e o gate terminal leem a **mesma** fonte de verdade.

---

## 0. Como este plano deve ser usado — leia antes de executar qualquer linha

**Este plano não se implementa cegamente.** Ele foi escrito com medição própria de
disco, cinco investigações paralelas e uma refutação adversarial — e **mesmo assim
errou**, em público, dentro deste documento: eu disse que a borda bloqueava o CSS
(era o handler do Go), que `cmd/social` não podia importar `internal/content` (já
importa), que campo sem borda resolveria contraste (dá 1,20 e reprova o gate), que
o embed dispensaria o gate de drift (não dispensa). Cada um desses erros teria virado
código errado se alguém executasse a linha sem medir.

A regra, então, vale para mim e para todo agente que este plano dirigir:

1. **Seguir o plano, com crítica.** Ele é a melhor hipótese disponível hoje, não
   verdade revelada. Antes de escrever, leia o alvo no disco: o arquivo, a linha, o
   dado vivo. Comentário não é fonte; plano também não.
2. **Medição vence o plano, sempre.** Se o disco contradiz este documento, o disco
   está certo — corrija o plano na mesma sessão, com o motivo escrito, e siga. Foi
   assim que as três provas erradas do manifesto (§4) apareceram.
3. **Contexto novo reabre decisão.** Várias decisões daqui foram tomadas com o que se
   sabia às 3h da manhã de 2026-09-05. Se uma medição posterior mostrar que o
   trade-off era outro, mude — e registre o porquê. Insistir num desenho que a
   medição já derrubou é o oposto de engenharia.
4. **O `advisor` é consultado sempre**: antes de abrir cada frente, ao mudar de
   abordagem, quando a medição contrariar o esperado, e antes de declarar qualquer
   coisa pronta — com o entregável já durável no disco. Ele já corrigiu o rumo desta
   sessão quatro vezes (a fronteira de honestidade, os códigos de recuperação, o
   `suspenso` com motivo, a colisão de `socialdb`). Chamar pouco custa retrabalho que
   o dono paga.
5. **Refutação antes do que é caro de reverter.** `Agent` com `model: fable`, pedindo
   REFUTAÇÃO com evidência — nunca "o que você acha". Concordância entre agentes não
   é verificação; refutação tentada e falhada é.

**Como este documento foi produzido**, porque isso é o que sustenta a confiança nele:
medição própria do disco antes de qualquer delegação · cinco investigações paralelas
(backend, borda, CSS, processual, monetização) · três desenhos de prova (regressão,
funcional, bots) · três refinamentos (lacunas, produto, acesso de bots) · refutação
adversarial · e o advisor consultado a cada mudança de rumo. **Todo relatório de
agente foi conferido no disco antes de entrar** — foi assim que apareceram os sete
buracos da §1.3, as três provas erradas da §4, o comentário que mente sobre os bots e
os dois falsos alarmes que desfiz. Nenhuma linha aqui entrou por alegação de terceiro.

---

## 1. Aditivo ao manifesto — sem isto, "tudo entra no plano" não vira nada

`content/redesocial_entregas.json` é o que o gate `redesocial-entrega-final` cobra.
Entrega que não está lá não existe para o guardião. **Primeiro ato pós-aprovação**:
acrescentar os IDs abaixo, no schema existente (`pacotes_go`, `arquivos`, `gates`,
`textos_em_arquivo`, `testes_minimos`), todos nascendo `pendente`. Nenhum ID
existente é apagado ou renomeado.

### 1.1 Frente FD — design premium dark (nova, 9 entregas)

| ID | Entrega | Prova |
|---|---|---|
| `FD-design-tokens` | Sistema de design "Ônix & Ouro" em tokens CSS, fonte única em Go | `pacotes_go: internal/socialtema`, `testes_minimos: 8` |
| `FD-css-servido-com-hash` | `wj-social-<hash>.css` servido pelo `cmd/social` sob **`/redesocial/assets/css/`** — o caminho que a CSP autoriza —, com o hash **no nome do arquivo**, não como token `'sha256-'` | `pacotes_go: internal/socialtema`, `gates: social-csp` |
| `FD-contraste-medido` | Contraste WCAG AA ≥4.5:1 **calculado em teste**, não afirmado | `pacotes_go: internal/socialtema`, `testes_minimos: 6` |
| `FD-tela-feed` | Feed de duas bandas renderizado, ≤50 KB, sem JS | `pacotes_go: internal/socialrender` |
| `FD-tela-thread` | Dúvida + respostas + paginação em 12 | `pacotes_go: internal/socialrender` |
| `FD-tela-perfil` | Perfil público de advogado e de leigo | `pacotes_go: internal/socialrender` |
| `FD-tela-conta` | Cadastro, entrada, confirmação, recuperação | `pacotes_go: internal/socialrender` |
| `FD-tela-painel` | Área autenticada (noindex por natureza) | `pacotes_go: internal/socialrender` |
| `FD-acessibilidade-por-fixture` | Teste renderiza fixture de **cada** tela e reprova `SevImportant` | `pacotes_go: internal/socialrender`, `testes_minimos: 8` |

### 1.1-bis Frente FP — o que faz a rede social ser usada (nova, 23 entregas)

O manifesto cobre conformidade e infraestrutura com rigor, e **não cobre produto**.
Estas nascem do refinamento, cada uma com a régua da OAB que respeita:

| ID | Entrega | Por que decide |
|---|---|---|
| `FP-gate-tese-nao-caso` | detector do CED art. 42, I: aconselhamento ao caso concreto **sai do público** e é oferecido no canal privado | única classe de risco que **encerra** o projeto — atinge a inscrição |
| `FP-quarentena-nao-trava-o-produto` | `fonte_url` de domínio oficial não conta como link externo; abrir dúvida não depende de reputação | sem ela, nem advogado responde nem leigo pergunta |
| `FP-caixa-de-entrada-servidor` | notificação renderizada no servidor, com vocabulário fechado por `CHECK` | sem canal de retorno, o funil é de uso único |
| `FP-atom-por-tema-e-por-duvida` | Atom por tema e por thread, público, sem conta | o único retorno que não depende de JS, e-mail ou terceiro |
| `FP-feed-privado-por-capacidade` | Atom do que você segue, por token revogável | põe a rede no leitor de feeds do usuário |
| `FP-consulta-corpus-publica` | 8.830 artigos, 754 súmulas, 2.384 precedentes servidos como página | o motivo de existir no dia 1, sem esperar a âncora |
| `FP-checagem-de-citacao` | cole uma citação e saiba se o artigo existe | a dor do momento — citação alucinada por IA já rendeu sanção |
| `FP-conferencia-de-prazo-do-advogado` | conferência de prazo **para o advogado verificado**, sobre ato do diário | `internal/prazo` já calcula e ninguém o chama — mas para o **leigo** seria consultoria (Lei 8.906, art. 1º, II) |
| `FP-antes-de-perguntar` | o formulário busca no acervo antes de abrir dúvida | entrega valor **quando a rede está vazia**, e corta duplicata |
| `FP-agenda-de-prazos-ics` | prazos do DJEN como assinatura iCalendar | a única coisa que trabalha **fora** da plataforma |
| `FP-peca-com-fonte-conferida` | conferidor de citação preenche o `fonte_url` obrigatório | transforma o atrito do gate em serviço |
| `FP-comentario-de-autoridade` | jurista comenta **tema**, nunca caso | enche a página de tema antes da primeira dúvida |
| `FP-painel-de-tese` | precedente + súmula + artigos + páginas que os invocam | monta-se de dado que já está no disco |
| `FP-diversidade-de-respondente` | quem já respondeu muito entra por último **no aviso** | dilui a habitualidade do art. 42, I, sem tocar o feed |
| `FP-cartao-por-thread` | og:image por thread e perfil, com OAB no título | faz o CED art. 44 ser estrutural |
| `FP-convite-para-o-conteudo` | convite endereçado ao conteúdo, nunca ao advogado | compartilhamento sem captação |
| `FP-feed-com-banda-de-temas` | feed curto completa com temas, rotulados como tema | resolve a sala vazia **sem inventar conteúdo** |
| `FP-ancora-barata` | testar se a âncora cabe no bloco já neutralizado | pode destravar a onda 7 inteira |
| `FP-medicao-de-humano-real` | série que reconcilia os três instrumentos, com piso e método | hoje toda decisão de produto usa um número que não é gente |
| `FP-perfil-que-nao-vira-vitrine` | teste sobre a **página** provando ausência de nota, caso, preço | o que a OAB abre é a página, não o DDL |
| `FP-util-nao-agrega` | mutação provando que "resposta útil" não sobe ao perfil | a fronteira entre feedback e placar proibido |
| `FP-exportar-minha-thread` | o leigo baixa a thread para levar ao advogado | é o que a pessoa já faz, copiando e colando |
| `FP-digest-opt-in` | um template a mais, opt-in, só do que você segue | a melhoria que o Resend paga, e nada quebra sem ele |

**Duas medições próprias que dimensionam essas entregas, e uma delas corta a promessa
pela metade:**

- **8.830 artigos no corpus, e apenas 1.104 — 12,5% — passam do piso de 1.100
  caracteres** que `social_policy.json` fixa para indexação. Contei um a um. Logo **não
  é verdade** que o corpus vira 8.830 páginas indexáveis: o CC art. 1º é uma frase. O
  desenho honesto é indexável o que passa sozinho (os 1.104 longos e os precedentes,
  que carregam tese e ementa), com o resto nascendo `noindex,follow`, agregado por
  capítulo ou enriquecido com a co-citação. A superfície indexável nova é da ordem de
  **milhares, não de dez mil** — e o motivo de visita continua de pé para os 8.830.
- **`internal/feed` já tem `BuildDocument` (`:79`), `RenderAtom` (`:198`) e
  `RenderRSS` (`:266`)**, com validação e teto de 1.000 entradas. `F2-feed-xml-separado`
  e `FP-atom-por-tema-e-por-duvida` deixam de ser código novo e viram adaptador.

**O que fica de fora, com o dispositivo:** ranking e nota de advogado (Prov. 205
art. 5º — já é trava de código, `reputacao.exibida_publicamente: false`) · vitrine de
casos e depoimento (CED art. 42, IV) · tabela de honorário e "primeira consulta
grátis" (Prov. 205 art. 3º — a **única** vedação literal do `social_policy.json`) ·
medalha, streak e placar de quem mais responde (art. 5º, e pioram o art. 42, I) ·
selo "especialista" (`checkSpecialistClaim` já reprova) · push ao **leigo** de
"advogados na sua área" (CED art. 40, VI — ao advogado é lícito, ao leigo não).

### 1.2 Decomposição de `F2-conteudo` (o ID pai fica, ganha filhos)

`F2-conteudo` hoje é uma linha só para a maior peça de engenharia do projeto.
Filhos, cada um com prova própria: `F2C-schema` (dúvidas, respostas, threads,
follows polimórficos, perfis, temas) · `F2C-feed-determinista` (duas bandas,
`(banda, data)`, §13.4) · `F2C-fts5` (busca no SQLite social) · `F2C-handlers`
(PRG, CSRF, sessão — a carroceria HTTP) · `F2C-follows` (assimétrico, alvo
polimórfico `conta|tema|area|duvida`, §13.5).

### 1.3 Entregas de carroceria que o manifesto pressupõe mas não nomeia

Sete buracos que **verifiquei por leitura própria**, não por relatório. Cada um
faria a fase parecer pronta e não funcionar — e um deles eu mesmo tinha diagnosticado
errado, o que é a razão de a §0 existir:

**E dois falsos alarmes que a verificação desfez, dignos de registro porque teriam
virado trabalho inútil:** o deploy **não** apaga o banco social (`CACHE_DIR` é
`var/on-demand-cache`, `deploy-publico:38` — `var/social/` fica intocado), e o backup
**já** é correto (acima). Duas entregas que eu ia criar e não existem.

| ID novo | O buraco, medido | Onde |
|---|---|---|
| `FX-kek-lida` | `WIKI_SOCIAL_KEK` **nunca é lida** — existe só como comentário em `internal/contas/contas.go:86`. `Abrir` exige `Chave` de 32 bytes e ninguém a fornece; `.env.local` tem 8 variáveis e **não** a inclui. A unit traz `EnvironmentFile=-`, e o `-` faz a ausência **não** ser erro: o serviço sobe sem chave e a falha só aparece no primeiro cadastro. **O padrão da casa já existe e é o que sigo:** `cmd/generate-oauth-client:54` emite `WIKI_OAUTH_SIGNING_KEY=<base64url>` para o dono colar, e sem ela as rotas de OAuth respondem 404 em vez de JSON de erro (DEC em `DECISIONS.md:383`). Então: `cmd/generate-social-kek` emite a chave, e sem ela o `cmd/social` **sobe servindo a superfície pública** — que não precisa de conta — e **recusa** as rotas de conta com 503 explícito. Degradar é honesto; subir e falhar no cadastro, não | `cmd/social`, `cmd/generate-social-kek`, `.env.local`, unit |
| `FX-contas-ligado` | `cmd/social` **não importa** `internal/contas`. Não existe `contas.db` no disco, nem constante que o nomeie (`superficie.go` só conhece `social.db` e `lgpd.db`) | `cmd/social/superficie.go` |
| `FX-email-saida` | `email_saida` existe como **uma linha de comentário** (`contas.go:24`) e mais nada. Sem a tabela, conta nasce `nao_confirmada` e **não há caminho para `ativa`** — `Entrar` barra com `ErrContaNaoConfirmada` | `internal/socialmail` |
| `FX-art18-executor` | `lgpd.Planeja` (`art18.go:242`) devolve um `PlanoDeExecucao` e **não existe `Executa`/`Aplica`**. O pacote sabe o que fazer e nada o faz | `internal/lgpd` |
| `FX-moderacao-operavel` | Não há listagem paginada de fila (só `ContagemPorFila`, `RevisarPrazos` das atrasadas e `FilaPorID` um a um) nem conceito de papel de revisor — `revisor_id` é string livre | `internal/moderacao` |
| `FX-schema-versionado` | Só `lgpd` grava versão de schema e falha fechado ao divergir (`banco.go:23`). `contas.SchemaVersion` e `moderacao.SchemaVersion` são constantes **mortas** — nada as grava, nada as confere | `contas`, `moderacao` |
| `FX-restore-prova-o-banco` | **O que mais me preocupa desta lista.** Existe `tools/check-backup-restauravel` e um timer semanal (`wikijuridica-backup-restore.timer`) — mas procurar por `social`, `.db` ou `sqlite` no gate devolve **zero**: ele prova que o repositório restaura, e **não** que o banco de contas restaura. O banco social é `sole-copy` — o git não o guarda, por ser dado pessoal — então backup que nunca foi restaurado é uma promessa, não uma garantia. A entrega: o gate abre a cópia restaurada, roda `integrity_check`, confere que as tabelas existem e que uma linha semeada volta legível **com o `.sal` certo** — porque restaurar o `.db` sem o sal devolve pseudônimos que não resolvem | `tools/check-backup-restauravel` |
| `FX-backup-com-trilha` | **Corrigi meu próprio achado.** Eu ia propor "criar o backup do banco social" porque `internal/socialbackup` não tem chamador em `cmd/`. Mas `tools/generate-backup-wiki:106-180` **já copia** `var/social/*.db` com `VACUUM INTO`, **falha fechado** se `sqlite3` faltar (não cai para `cp`, que produziria arquivo que abre e mente), copia o `.sal` junto e roda `PRAGMA integrity_check` na cópia. O timer rodou há 2 h. O que falta é **trilha**: o ledger `backup_wiki.jsonl` não tem campo nenhum sobre os bancos sociais — não há como provar, lendo o ledger, que o dado de usuário foi salvo e passou no integrity check | `tools/generate-backup-wiki`, `data/ops/backup_wiki.jsonl` |

### 1.4 Quatro defeitos vivos que a investigação achou — e que entram como P0

Nenhum deles está no manifesto. Os quatro verifiquei no disco.

**(a) `/redesocial/` já serve visitante real, sem CSS.** `data/ops/access/nginx-2026-09-05.jsonl`
registra hoje `GET /redesocial/` → **200**, cache **HIT**, de um Android/Chrome via
Cloudflare. A superfície está pública. O design deixa de ser cosmético: é o que uma
pessoa real está vendo agora.

**(b) `wikijuridica-social` está `linked`, não `enabled` — um reboot derruba a rede
social e ela não volta.** `systemctl is-enabled` devolve `linked` para o `.service` e
o `.socket`; `sockets.target.wants/` tem `wikijuridica-server.socket` e
`multi-user.target.wants/` tem `wikijuridica-server.service` e `-nginx.service` —
**nenhum dos dois sociais**. Está no ar porque foi iniciado à mão. Depois de um
reboot, `/redesocial/` e `/api/v1/redesocial/` devolvem 502 até alguém intervir.
Entrega `FX-unit-enabled`, e é o primeiro comando da onda 1.

**(b-bis) Nenhum vigia observa a rede social.** `grep 8091 tools/check-http-smoke` e
`tools/check-portal-health` devolvem **zero** nos dois. O portal tem timer de saúde,
watchdog e smoke — e nenhum deles olha para o 8091. Somado ao `linked` acima: a rede
social pode cair, ou não voltar de um reboot, e **nada avisa**. `F1-deploy-conhece-dois-servicos`
já prevê o segundo alvo no vigia; acrescento o smoke, que hoje passa verde com a rede
social morta.

**(c) A CSP privada é sobrescrita pela pública em toda leitura autenticada.** A
`location ^~ /redesocial/` inclui `social-headers-publico.conf` **estaticamente**,
para toda resposta. O Go escolhe a política por cookie (`rotas.go:189-207`), mas
`more_set_headers` sobrescreve cabeçalho do upstream. Hoje o dano visível é só o
`Referrer-Policy` do logado virar o do anônimo — porque as duas CSPs são idênticas
byte a byte. No dia em que a pública ganhar host de terceiro (receita que
`socialheaders.go:81-87` já descreve), um usuário logado passa a receber a CSP
**pública**. Entrega `FX-csp-privada-nao-sobrescrita`, com gate.

**E uma correção ao plano original:** ele fala em "4 locations novas", mas a §7.1-bis
nomeia **três** blocos (leitura, assets, escrita) — os itens (5) e (6) são exigências
de diretiva aplicadas a eles, não locations. Das três, **duas já existem** e
funcionam: `^~ /redesocial/` (linha 1666, com `proxy_cache wj_social`,
`proxy_cache_bypass $cookie_wjsession`, zero `limit_req`) e `^~ /api/v1/redesocial/`
(linha 1705, `limit_req zone=wj_social_escrita` em `$binary_remote_addr`,
`proxy_cache off`). **Falta uma:** `^~ /redesocial/assets/`. O arquivo vivo é
`ops/nginx/standalone/nginx.conf` — `ops/nginx/wikijuridica.conf` traz banner
"NÃO-CARREGADO-EM-PRODUÇÃO" e auditá-lo daria verde sobre config que ninguém carrega.

**Uma entrega já está satisfeita e o tracker não sabe; a irmã dela eu quase declarei
pronta por engano.** `ops/cloudflare/dynamic-redirect-rules.json` **já exclui**
`/redesocial/assets/` do redirect de barra final — `F05-dynamic-redirect-preserva-assets`
vira `entregue` na onda 0, com a prova apontada. Mas `F05-edge-redirect-drift` **não**:
o gate existe e passa (exit 0, "1 regra confere com a zona"), e eu ia dá-lo por
fechado — só que `grep redesocial tools/check-edge-redirect-drift` devolve **zero**.
Ele confere o `/assets/` do acervo e **não prova nada** sobre o social. Gate verde
sobre o que ele não mede é precisamente a R2. Estendê-lo é trabalho real, e a prova do
manifesto (que exige a string `/redesocial/assets/` dentro do gate) estava certa desde
o começo.

**O sitemap adicional também já tem o motor pronto:** `crawl.AdditionalSitemapPaths`
existe e é testado (`crawl.go:134`, `sitemap_adicional_test.go`) — falta só a chave em
`content/crawl_policy.json`, que hoje **não está lá**. Mas preenchê-la na onda 1,
como eu havia planejado, apontaria o `robots.txt` para um `/redesocial/sitemap.xml`
que devolve 404 até a onda 4 — incidente no Search Console por antecipação. Ela vai
junto com o sitemap, na onda 4.

`F05-cache-rules-exclui-redesocial` precisa do motivo reescrito: `cache-rules.json`
usa `edge_ttl: respect_origin`, e o Go já emite `private, no-store` para sessão — a
proteção existe por outro mecanismo, e a entrega passa a ser **provar isso com gate**,
em vez de acrescentar uma exclusão redundante.

**E varri as 128 provas contra o disco** (onda 0 antecipada): **zero** entregas
marcadas `entregue` têm prova que não casa — o guardião é honesto. Das pendentes, 43
provas textuais não casam, e a leitura de cada uma diz o que é: 20 apontam para
arquivo que já existe e só falta a linha (`content/pages.json` para as páginas legais,
`ops/nginx/standalone/nginx.conf` para a location de assets, `go.mod` para o
renderizador de QR, três DECs a redigir), e o resto aponta para arquivo que ainda não
nasceu. Nenhuma é falsa. A única prova **errada** achada até agora é a de
`F4-intimacao-multitenant` (§4).

### 1.5 A onda 0, medida agora — dois números que o plano de ontem já não descreve

`codex2-policy-enforcement` reprova hoje com **234** falhas, não as 273 que o
`PLANO_REDE_SOCIAL.md` registrou em 2026-09-04: a correção de causa raiz
(`P0-policy-registro-derivado-do-gomod`) já derrubou 39. O baseline
(`data/ops/codex2_policy_baseline.json`) **não existe** — sem ele, regressão nova é
indistinguível de dívida herdada, e é isso que `P0-baseline-policy` fecha. As duas
maiores classes (75 `external_dependency_unapproved`, 56
`runtime_candidate_module_unapproved`) nada têm com a rede social.

**Mas três escapes de sqlite são reais, e um é nosso:**
`internal/moderacaotransparencia/transparencia.go` — pacote **da rede social** — abre
o `social.db` direto e **não está na allowlist** de `moderncSQLiteImportAllowed`
(`policy.go:812`). A allowlist cobre `cmd/social/`, `internal/{contas,moderacao,lgpd,
socialdb,socialconteudo,sigilo,socialbackup}/` — e **nenhum** dos outros 12 pacotes
novos que vou criar. `F1-sqlite-import-allowlist` está marcado pendente e na verdade
já foi feito para os que estão lá; o trabalho real é **estendê-la** aos que faltam,
antes de a onda 2 escrever o primeiro import, senão cada pacote novo chega
reprovando.

Mais a carroceria propriamente dita: `FX-handlers-conta` (cadastro/entrada/OTP/
recuperação sobre `AutorizaMudancaDeEstado`, que já recebe `*http.Request` e é a
porta pronta para handler) · `FX-handlers-moderacao` · `FX-sessao-http` (cookie
`wjsession` — `contas.CookieDeSessao` já existe em `sessao.go:328`) ·
`FX-erro-e-404` (hoje texto puro, passa a ter o design).

---

## 2. Caminho crítico do design — o bloqueio é o handler do Go, não a borda

Escrever CSS bonito primeiro seria trabalho jogado fora. Mas **corrijo o diagnóstico
que eu tinha**: a borda não bloqueia nada. `location ^~ /redesocial/` usa prefixo, e
prefixo casa todo subcaminho — inclusive `/redesocial/assets/css/*`, que já chega ao
8091 hoje. O que devolve 404 é o catch-all do próprio Go (`rotas.go:59`): **não existe
handler de asset nenhum**. A location dedicada continua valendo, mas por outro motivo
— política de cache: hoje a herdada é `proxy_cache_valid 200 10m`, e uma folha
`immutable` merece um ano. Isso é otimização, não desbloqueio.

A ordem é obrigatória e cada elo tem uma falha silenciosa própria:

```
1. location ^~ /redesocial/assets/  A ÚNICA que falta das TRÊS (não quatro — ver
                                    §1.4). proxy_pass 8091, immutable de 1 ano.
                                    A Cloudflare já isenta esse caminho do 301
                                    de barra final: esse elo está feito.
2. handler de asset em cmd/social   HOJE NÃO EXISTE NENHUM: /redesocial/assets/...
                                    cai no catch-all e devolve 404 em texto puro.
3. internal/socialtema              tokens como CONSTANTES GO (jamais var(--x)),
                                    folha montada por concatenação, como o acervo.
4. hash de conteúdo                 sha256 truncado em 16 hex — o padrão de
                                    render/stylesheet.go:132. Nome derivado do
                                    conteúdo, nunca escrito à mão.
5. socialheaders.PrefixoDeEstilo    vira a URL EXATA da folha e o prefixo de
                                    diretório deixa de existir — o próprio
                                    comentário do arquivo já manda fazer isso.
6. os DOIS .conf, byte a byte       socialborda/csp.go compara literalmente, e
                                    cmd/generate-csp-nginx NÃO cobre os sociais:
                                    hoje a edição é manual. Passa a cobrir.
7. <link> em cmd/social/render.go   rotas_test.go:66 proíbe <style e style=,
                                    NÃO proíbe <link> — a folha externa passa.
8. auditoria de acessibilidade      AuditDocument está hardcoded a
                                    render.StylesheetPath() e daria
                                    a11y_stylesheet_unresolved BLOQUEANTE numa
                                    folha social. Precisa aprender a resolvê-la.
```

**O buraco que ninguém tinha visto: hoje nenhuma auditoria de acessibilidade toca o
`cmd/social`.** `cmd/check-accessibility-html` varre `public/`, e a rede social não
escreve em `public/` — serve dinâmico. As regras de contraste **já existem**
(`accessibilityaudit/rules.go:696` para o SC 1.4.3 e `:745` para o 1.4.11); falta
**ligá-las**. Isso muda `FD-contraste-medido` de "escrever teste novo" para "estender
o auditor e chamá-lo sobre fixture de cada tela" — mais barato e mais forte, porque
reusa um auditor já provado sobre dez mil páginas.

**Duas correções que a investigação impôs ao plano, e que eu conferi no disco:**

**(i) O caminho é `/redesocial/assets/css/`, não `/redesocial/assets/`.**
`socialheaders.go:50` fixa `PrefixoDeEstilo =
"https://wikijuridica.com.br/redesocial/assets/css/"` — e o comentário explica o
subdiretório: a location vai servir **CSS, JS e avatar juntos**, e autorizar
`/redesocial/assets/` inteiro em `style-src` daria a qualquer arquivo enviado por
visitante o direito de ser interpretado como folha de estilo. É `'self'` reintroduzido
com escopo de diretório — exatamente o que o contrato proíbe. **Requisito que isso
impõe:** nenhum upload pode ser gravado sob `.../css/`. O mesmo comentário já diz o
alvo: *"quando a folha nascer com hash no nome, esta constante vira a URL exata dela
e o prefixo deixa de existir"* — trocar prefixo por URL exata é a entrega, não um
detalhe.

**(ii) `var(--x)` está PROIBIDO, e o motivo derruba o desenho óbvio.**
`internal/render/render.go:1959-1965`: nenhuma custom property de cor ou tamanho,
porque `cmd/check-accessibility-html` faz uma mini-cascata com parser próprio que só
entende literais — `color:var(--x)` faria o gate de contraste medir a **cor herdada**
e **aprovar por engano**. Um gate de acessibilidade que aprova por engano é pior que
não ter gate. Logo: os tokens da tabela abaixo vivem como **constantes Go** em
`internal/socialtema`, e o CSS servido sai com os **literais interpolados** — a
disciplina de token fica na fonte, e o auditor enxerga a cor real. É também o que
separa este design do `docs/design/premium-nav-gold-reference.min.css`, que usa ~25
custom properties e por isso é rascunho, não a folha de produção.

**O elo 6, examinado a fundo, porque é onde um agente travaria.** A refutação alertou
que tornar `PrefixoDeEstilo` uma URL derivada do hash faria o gate
`social_csp_literal_no_go` reprovar. **Li o gate e não é isso:**
`socialborda/csp.go:242` reprova o **call site** — `header.Set("Content-Security-Policy",
"…")` com string literal — e exige que o argumento seja `socialheaders.X`. Uma
constante calculada dentro de `socialheaders` continua passando, porque o call site
não muda. O gate está certo e não precisa de exceção.

O elo que falta é outro, e é o mesmo do acervo: se a constante é calculada, o `.conf`
tem de ser **gerado a partir dela**, não editado à mão. `cmd/generate-csp-nginx` já
faz exatamente isso para `ops/nginx/security-headers.conf` e hoje **não cobre** os dois
`.conf` sociais — por isso a edição social é manual e só o teste de drift a pega.
Estendê-lo aos dois é a entrega, e é melhoria que o repositório inteiro aproveita.

**Onde a folha é servida — decisão minha, com uma ressalva que a refutação impôs:**
**embutida no binário** (constante Go, como o acervo faz em `render/stylesheet.go`) e
servida pelo `cmd/social`, não por `root public/`. O isolamento vale nos dois
sentidos: a rede social não depende do deploy do acervo para ter estilo. **Mas eu
havia escrito que isso tornaria o drift "impossível por construção", e é falso:** a
CSP que o navegador vê vem de `more_set_headers` no `.conf`, que **substitui** o
cabeçalho do upstream — o valor derivado no Go nunca chega ao browser. Então cada
mudança de CSS continua exigindo editar `socialheaders.go` **e** os dois `.conf`, com
o gate de drift de `socialborda/csp.go` guardando o par. O embed compra isolamento e
nome derivado do conteúdo; não compra dispensa de gate. `location ^~
/redesocial/assets/` faz `proxy_pass` para 8091 com `immutable` de um ano.

**Teto da folha: 13.000 bytes**, o mesmo `ExternalCSSBudgetBytes` do acervo
(`htmlcontract.go:73`) — não os 16 KB que eu havia estimado. O acervo usa 12.117 em
13.000; a rede social tem mais telas mas nenhuma justificativa para um teto maior, e
teto próprio (não importado) preserva o isolamento entre os binários.

### O sistema de design: "Ônix & Ouro"

Continuidade de marca com o acervo (`docs/design/premium-nav-gold-reference.min.css`:
navy `#0F1D2E`, gold `#C6A253`, serif nos títulos), invertido para dark como **base**
— não como `@media prefers-color-scheme`. O dono pediu dark, não dual.

Paleta com contraste **calculado** (WCAG 2.x, fórmula de luminância relativa), não
afirmado. A primeira tentativa reprovou e foi corrigida — está aqui como prova de que
o número saiu de medição:

| Token | Valor | Contraste sobre `bg` / `surf-1` / `surf-2` | Papel |
|---|---|---|---|
| `--bg` | `#0A0F16` | — | fundo, quase-preto de temperatura fria |
| `--surf-1` / `--surf-2` | `#111925` / `#18222F` | — | card; hover e destaque |
| `--ink` | `#E8EDF3` | 16,32 / 15,00 / — | texto principal |
| `--ink-2` | `#A3B0BF` | 8,71 / 8,00 / 7,27 | secundário |
| `--ink-3` | **`#8494A3`** | 6,17 / 5,67 / 5,15 | metadado — **corrigido**: o `#6F7D8C` inicial dava 4,19 sobre `surf-1` e **reprovava AA** |
| `--gold` | `#C6A253` | 7,96 / 7,31 / 6,64 | acento de hierarquia e foco — **nunca** texto de corpo |
| `--link` | `#7FB7E8` | 9,01 / 8,27 / — | link |
| `--rule` | `#1E2A38` | 1,32 | separador **decorativo** |
| `--rule-controle` | `#5A6E86` | 3,67 / 3,37 / — | borda de campo e botão — o piso do SC 1.4.11 |
| `--ok` | `#6FC58F` | 9,20 / 8,46 / 7,69 | confirmação |
| `--warn` | `#EF9838` | 8,44 / 7,75 / 7,08 | atenção |
| `--danger` | `#E8836F` | 7,24 / 6,65 / 6,04 | erro |

**Por que o `--warn` é alaranjado e não âmbar:** o candidato óbvio (`#E0B457`, 9,92)
tem **matiz 41 — idêntico ao do `--gold`**. Dois papéis diferentes com a mesma cor é
como um design premium vira confuso: o leitor não sabe se a pastilha é acento de
hierarquia ou aviso. `#EF9838` afasta o matiz em 10 graus e mantém 8,44. E, de todo
modo, **nenhum dos três carrega significado sozinho** — sempre acompanham filete
lateral e texto, que é o que a técnica G183 exige de quem não distingue cores.

**A decisão sobre a borda — e o erro que a refutação adversarial pegou em mim.** Eu
havia escrito que, como nenhum filete escuro chega aos 3:1 do SC 1.4.11 (testei até
`#42566C`, 2,54), campo e botão se distinguiriam **por superfície**, com `surf-2`
sobre `bg`. **Medi: isso dá 1,20** — pior que a borda que eu rejeitava. E a regra que
reprovaria está escrita e ativa: `accessibilityaudit/rules.go:765-772` acusa
`a11y_control_boundary_contrast_below_aa` com severidade **`SevImportant`** para
"campo sem borda e com fundo X sobre Y" abaixo de 3:1 — a mesma severidade que
`FD-acessibilidade-por-fixture` promete reprovar. Todo `<input>` de toda tela
falharia o gate do próprio plano.

**A correção: dois tokens de borda, com papéis distintos e piso medido.**
`--rule #1E2A38` (1,32) continua como separador **decorativo**, que a norma não cobra;
e nasce `--rule-controle #5A6E86` — **3,67 sobre `bg` e 3,37 sobre `surf-1`**, acima
do piso nas duas superfícies — para a borda de campo e botão, que é o único indicador
de onde se digita. O foco continua dourado (7,96). Elevação por superfície e filete,
nunca por sombra pesada: em dark, sombra é o que denuncia amadorismo.

**Tipografia.** Serif (Georgia, "Times New Roman", Noto Serif, Liberation Serif) nos
títulos — autoridade jurídica —, sans de sistema no corpo, as mesmas pilhas do acervo,
zero web font (nenhum recurso externo, que é regra do projeto e também o que mantém a
página abaixo do teto). Escala, com o porquê de cada passo:

| Papel | Tamanho / altura | Decisão |
|---|---|---|
| corpo | `1.0625rem` / `1.7` | igual ao acervo — texto jurídico é lido, não escaneado |
| metadado, rótulo | `0.875rem` / `1.5` | um degrau abaixo, nunca dois: abaixo disso vira letra miúda de contrato |
| título de card | `1.125rem` / `1.35` serif | precisa competir com o corpo sem virar manchete |
| H1 da thread | `1.5rem` → `1.75rem` acima de 48rem / `1.25` | uma única quebra de breakpoint, no mesmo ponto do acervo |
| H2 de seção | `1.25rem` / `1.3` serif | — |
| versalete da navegação | `0.8125rem`, `letter-spacing: .08em`, maiúsculas | o mesmo tratamento do cabeçalho do acervo |

Duas medidas que separam texto jurídico legível de blog: `max-width` de **68ch** na
coluna de leitura (o acervo usa 60ch; a thread tem citação e recuo, e ganha um pouco
mais) e `text-wrap: pretty` com `hyphens: auto` no corpo — títulos levam
`text-wrap: balance` e `hyphens: manual`, porque hifenizar um título de tese é feio e
atrapalha a leitura por máquina.
**Sem avatar** (§13.6): `<span>` com iniciais, `aria-hidden` — economiza 1,4 KB/tela,
elimina uma classe de achados de acessibilidade e dispensa `img-src` na CSP.
Orçamento: ≤16 KB minificado (o acervo usa 12,1).

O teste de contraste (`FD-contraste-medido`) **recalcula** essa tabela a partir dos
tokens e reprova o commit se um par cair abaixo do piso — o número não pode
envelhecer no comentário enquanto o CSS muda.

### Os doze componentes, e por que são só doze

Vinte e uma telas com componentes ad hoc viram vinte e uma linguagens visuais. O
sistema é fechado: **doze componentes**, e tela que precisar de um décimo terceiro
justifica no commit.

| Componente | Forma | A decisão que carrega |
|---|---|---|
| **Cabeçalho** | marca em serifa, navegação em versalete com `letter-spacing`, filete dourado de 2px na base | espelha o do acervo invertido para dark — continuidade de marca sem copiar o arquivo |
| **Card de dúvida** | `<article>` em `surf-1`, título em serifa, metadado em `--ink-3`, área e tempo | `<article>` **não é landmark**; `<section aria-label>` viraria `region` e vinte deles seriam vinte landmarks idênticos |
| **Bloco de resposta** | recuo à esquerda com filete, autor, selo, corpo, fontes citadas | as fontes ficam **visíveis**, não em nota — é o que sustenta o E-E-A-T e o que o `oabgate` exige |
| **Selo de verificado** | pastilha discreta em `--gold` com "OAB/UF nº" | texto, nunca ícone sozinho: leitor de tela e busca precisam da inscrição literal (CED art. 44, §1º) |
| **Iniciais** | círculo de 2rem, `--surf-2`, iniciais em `--ink-2`, `aria-hidden` | **não é avatar** — economiza 1,4 KB/tela, dispensa `img-src` e elimina uma classe de achados |
| **Formulário** | campo em `surf-2` com borda `--rule-controle` (3,67:1), rótulo acima, erro abaixo em `--danger` | borda de controle é o único indicador de onde digitar: abaixo de 3:1 o gate reprova (`rules.go:765`) |
| **Botão** | primário em `--gold` sobre `--bg`; secundário como contorno | dourado é **acento**, então botão primário é um por tela; mais que isso destrói a hierarquia |
| **Paginação** | "anterior / 2 de 7 / próxima", `rel=prev`/`rel=next` | por caminho (`/pagina/2/`), nunca infinito — infinito exige JS e é invisível ao crawler |
| **Bandas do feed** | duas listas com título `<h2>`, sem aba, sem JS | aba exigiria JS ou duplicar conteúdo; título é o que o crawler entende |
| **Estado vazio** | texto que diz o que fazer, nunca ilustração | tema sem thread nasce `noindex,follow` — a tela vazia é honesta, não decorada |
| **Aviso** | faixa em `surf-2` com filete lateral colorido | `--danger`/`--warn`/`--ok` só aqui; em nenhum outro lugar cor carrega significado sozinha (G183) |
| **Rodapé** | responsável técnico, OAB, licença, link da gêmea `.md` | `Rafael Toledo, OAB/RJ 227191` sai de `content/site.json`, **nunca** hardcoded |

**Regras transversais, que valem para os doze:** nenhum `id` de lista sem o id da
entidade (`r-8412-corpo`) contra `ruleDuplicateIDs`; nenhum `<aside>` dentro de
`<main>`; formulário de ação em lista **sem** `aria-label` (o nome vai no `<button>`,
que não é landmark); `target="_blank"` só com o aviso no `aria-label` que a WCAG 3.2.5
exige. E o CSS sai por blocos nomeados, como `render/stylesheet.go:97-112` faz — a
tela que não usa um bloco não paga os bytes dele.

### O inventário de telas — o que "rede social de verdade" significa em rotas

Hoje existe **1**. A entrega são **21 rotas** + gêmea `.md` de cada pública. Rota que
não está aqui não existe (`cmd/social/rotas.go:44` — 404 honesto, nunca "em breve").

| Rota | Papel | Índice |
|---|---|---|
| `/redesocial/` | feed de duas bandas (§13.4) | sim |
| `/redesocial/duvida/{slug}/` + `/pagina/{n}/` | thread, 12 respostas por página | sim |
| `/redesocial/tema/{area}/{slug}/` | espelho das 10.141 rotas do acervo | sim, **após** a 1ª dúvida (§13.2) |
| `/redesocial/area/{area}/` | filtro por área (43 áreas) | sim |
| `/redesocial/perfil/{handle}/` | perfil de leigo, advogado ou jurista | sim |
| `/redesocial/blog/{slug}/` | post autoral | sim |
| `/redesocial/cursos/` | vitrine separada, **sem CTA advocatício** (CED 40, IV) | sim |
| `/redesocial/transparencia/` | encarregado, canal, série de moderação | sim |
| `/redesocial/sitemap.xml` · `/redesocial/feed.xml` | descoberta própria, **fora** do índice do acervo | — |
| `/redesocial/{cadastrar,entrar,confirmar,recuperar}/` | conta | **noindex** |
| `/redesocial/seguindo/` | feed filtrado por follows | **noindex** |
| `/redesocial/painel/` | intimações DJEN, prazos | **noindex** |
| `/redesocial/mensagens/` | mensageria cifrada (§15.5) | **noindex** |
| `/redesocial/conta/` | as 3 rotas do art. 18 LGPD | **noindex** |
| `/redesocial/moderacao/` | fila, só para quem modera | **noindex** |
| `/api/v1/redesocial/*` | **toda** escrita (o WAF bloqueia POST fora de `/api`) | — |

**Quatro papéis, e a separação é norma, não interface:** visitante · leigo (e-mail
confirmado) · advogado verificado (selo por JOIN com decisão vigente) · jurista —
juiz, promotor, delegado, professor. Os juristas entram como **autoridade de
conteúdo** e **não recebem caso**: LOMAN art. 36, I e EOAB art. 28 tornam isso
impedimento funcional, logo trava de código em `internal/socialpapeis`.

**Dois gates de ética diferentes, e confundi-los quebraria o produto:**
`AvaliarDuvida` (leigo) roda só `pii` + `publicidadenome` — rodar as 14 regras do
Prov. 205 sobre "meu caso é urgente" produziria falso positivo em massa;
`AvaliarComentario` (advogado) roda o `oabgate` completo, e por isso o formulário de
resposta **obriga** `fonte_nome` + `fonte_url` — sem eles `checkVeracity` é HARD e
bloquearia quase toda resposta (§13.3).

**Reaproveitamento medido — três coisas que um agente reescreveria por não saber que
existem:**

- `internal/socialcard` já gera og:image derivado da área de prática, sem literal por
  rota. Serve a thread social sem código novo.
- `internal/socialpolicy` é **fonte única** dos limites, com trilha datada
  (`content/social_policy.json`, vigente desde 2026-09-04): quarentena de 7 dias e 3
  posts, 5 posts/dia e 20 comentários/dia na quarentena, orçamentos de 20/100/200/200,
  a escala de reputação com as três destravas (link externo ≥5, mensagem a
  desconhecido ≥10, abrir thread ≥20) e `exibida_publicamente: false`. **`socialantiabuso`
  lê daqui e não inventa número nenhum** — número escrito no código é número que
  diverge do que a página de transparência publica.
- `cmd/social/pagina.go` já tem os utilitários de PT-BR que toda tela vai precisar:
  `dataPorExtenso`, `prazoPorExtenso`, `pluralDeDias`, `numeroComPonto`,
  `permitidoOuNao`. Reescrevê-los produziria duas grafias de data no mesmo site.

**E uma decisão de arquitetura que faltava:** o tipo `pagina` de hoje
(`pagina.go:22`) é um documento institucional — título, seções, itens, fontes. Ele
**não serve** para feed, thread ou perfil. `internal/socialrender` nasce com um tipo
por tela, e o `pagina` atual migra para lá como o caso "documento", junto com
`textoCorrido` (que é o que alimenta o `oabgate` no boot). Sem isso, ou as telas novas
forçam dados em um tipo que não os comporta, ou nasce um segundo renderizador ao lado
do primeiro.

---

## 3. As ondas

Regra: paralelos só em pacotes distintos. Commit agrupado **por onda**, não por
entrega — commit que toca Go dispara build de ~5 min sob `flock`, e dezenas de
commits serializariam a sessão inteira no lock.

| # | Onda | Entregas | Alvos | Prova |
|---|---|---|---|---|
| **0** | Destravar (eu, sequencial) | aditivo ao manifesto · as 3 provas erradas (§4) · `P0-baseline-policy` · `P0-molde-stf-informativo` · `FX-allowlist-alcanca-os-12` · melhorias 1 e 2 do guardião (§7) | `content/redesocial_entregas.json`, `data/ops/codex2_policy_baseline.json`, `internal/codex2policyenforcement/policy.go:4249`, `internal/redesocialcompletude/` | baseline gravado; allowlist alcançando os 12 pacotes novos; `completude` verde depois do aditivo |
| **1** | Infra de borda + fundação de dados | **`FX-unit-enabled` primeiro** · **`FB-causa-do-abandono`** · `F05-nginx-locations` (só falta a de assets) · `FX-csp-privada-nao-sobrescrita` · `F1-sqlite-pragmas` (+ o teste de `journal_mode == delete` do `lgpd`) · `FX-migracao-versionada` · `F1-deploy-conhece-dois-servicos` (+ vigia e smoke no 8091) | `ops/systemd/`, `ops/nginx/standalone/nginx.conf`, `internal/socialdb`, `tools/deploy-publico`, `tools/check-http-smoke` | `systemctl is-enabled` = `enabled`; **a causa dos 503 e do abandono nomeada com evidência**; `foreign_keys` provado **por conexão** |

**O que é `internal/socialdb` — e aqui o manifesto manda, não eu.** Sete provas o
amarram, e três delas exigem **DDL** dentro dele (`perfis_advogado`,
`UNIQUE(oab_numero, seccional)`, `'resposta'`), além dos três pragmas
(`foreign_keys`, `secure_delete`, `journal_mode`). Logo `socialdb` **não é** um pacote
só de DSN, como eu havia escrito: ele carrega o DSN, os pragmas **e** o schema do
domínio social. `socialconteudo` fica com a lógica — feed, follows, avaliação — e
recebe a conexão por `moderacao.Conexao()`, sem abrir um segundo pool sobre o mesmo
arquivo.

**A armadilha exata que isso cria, e ela é a §9.4 pela porta dos fundos:** a prova de
`F1-sqlite-pragmas-por-conexao` exige o literal `journal_mode` em `socialdb` — e o
valor lá será `WAL`. Um agente que importe `socialdb` no `lgpd` "para não duplicar"
leva o WAL junto e destrói o apagamento do art. 18, VI. Pior: **conferi, e nada pega
isso** — `lgpd.ConferePragmas` valida `foreign_keys` e `secure_delete` e **não**
`journal_mode`, e o teste que mede os bytes fecha a conexão antes de ler o arquivo, o
que em WAL dispara checkpoint e faz o teste **passar mesmo com WAL**. A mitigação não
pode ser um parágrafo no prompt do agente: é um teste de uma linha asserindo
`journal_mode == delete` para `lgpd.DSN()`, e ele entra na onda 1.
| **1'** | (paralela) Correio, DNS e recuperação | `F1-socialmail-ate-a-fronteira` · `FX-codigos-de-recuperacao` · `F1-confirmacao-em-dois-passos` · tier de conta não confirmada · **SPF/DKIM/DMARC publicados** | `internal/socialmail` (fila + transporte por interface + Resend), `internal/contas` (códigos de uso único), `tools/generate-cloudflare-token`, `tools/generate-dns-record` | fila grava na mesma transação; `dig` confirma os três registros no ar; senha esquecida deixa de ser conta perdida |
| **1'''** | (paralela) Continuidade | `FX-restore-prova-o-banco` · `FX-backup-com-trilha` · `FX-kek-lida` | `tools/check-backup-restauravel`, `tools/generate-backup-wiki`, `cmd/generate-social-kek` | a cópia restaurada abre, passa `integrity_check` e devolve uma linha semeada **com o sal certo** |
| **1''** | (paralela) F0 restante | `F0-transparencia` · `F0-paginas-legais` · `F0-transparencia-serie` · `F0-fechamento` | `internal/moderacao`, `content/pages.json` | `moderacao-honra-exige-ordem` + `promessa-privacidade-tem-substrato` |
| **2** | Domínio — a peça maior | `F2C-schema` · `F2C-feed-determinista` · `F2C-fts5` · `F2C-follows` | `internal/socialconteudo` (novo) | ≥20 testes; feed auditável por uma consulta SQL |
| **2'** | (paralela) Identidade | `F1-verificacao-de-oab` · `F1-papeis-com-impedimento-funcional` · `F1-registros-acesso-cifrados` · `F1-lista-de-senhas-comuns` · `F1-credential-stuffing` | `internal/verificacaooab`, `socialpapeis`, `registrosacesso`, `contas` | selo por JOIN com decisão vigente, nunca coluna de perfil |
| **2''** | (paralela) **Design** | `FD-*` (9) | `internal/socialtema` (novo), `internal/socialrender` (novo) | contraste **calculado**; fixture de cada tela sem `SevImportant` |
| **3** | Carroceria HTTP — **depende da 2'''''** | `F2C-handlers` · `FX-*` · `F1-html-template-contextual` · `F1-direitos-do-titular` | `cmd/social/` | cadastro real ponta a ponta; as 3 rotas do art. 18 no ar |
| **3'** | (paralela) Anti-abuso | `F2-anti-abuso-camadas-2-a-6` · `F2-conta-inautentica` · `F2-sse-com-teto` · `F2-avatar-reencodado` · `F2-varredor-de-retencao` | `internal/socialantiabuso`, `socialavatar` | ≥12 testes; quarentena persistida |
| **4** | Indexação e canal de máquina | `F2-indexacao` · `F2-sitemap-fora-do-indice` · **`F05-sitemap-adicional` (movido da onda 1)** · `F2-feed-xml-separado` · `F2-indexnow-por-transicao` · `F2-lastmod-causal` · `F2-paginacao` · `F2-qapage-condicional` · `F2-gemea-licenca` · `F2-canal-de-maquina` (por loopback) · `F2-piso-comparativo` · `F2-acessibilidade-de-lista` | `internal/socialindexnow`, `content/crawl_policy.json`, `cmd/social` | `social-indexavel` + `social-bots` verdes |
| **5** · *sessão 2* | Sigilo e conexão | `F3-*` (9) | `internal/sigilo`, `socialconexao`, `notify`, `intake` | ≥15 testes; `sigilo-sem-texto-claro` e `social-sem-chave-no-ambiente` |
| **5'** · *sessão 2* | (paralela) Processual | `F4-*` (7) | `internal/datajudfila`, `internal/djen` | DataJud < 1 s percebido contra os 28 s do CNJ |
| **6** · *sessão 2* | Ponte editorial e consulta | `F5-*` (6) | `internal/consultapublica`, `internal/ponteeditorial` | `ponte-editorial-sem-autoria` |
| **6'** · *sessão 2* | (paralela) Monetização | `F6-*` (5) | Pix, OFX, cursos | conciliação sem gateway |
| **7** · *sessão 2* | **Âncora do acervo** (irreversível) | `F2-ancora-acervo` | 10.141 rotas, robots, purga ampla | refutação Fable **antes**; só depois de `/redesocial/tema/…/` responder 200 |
| **8** · *sessão 2* | Fechamento | `F*-fechamento` (6) | — | `check-redesocial-entrega-final` **verde, zero pendentes** |

**Onde a sessão 1 termina, e como a sessão 2 sabe que começou.** A sessão 1 fecha as
ondas **0 a 4** mais as cinco `FP-*` que decidem se o produto funciona (§ *O escopo
honesto*). As ondas marcadas *sessão 2* não são desta passada — e o marcador existe
porque um executor que leia só a tabela não teria como saber onde parar, que é o
defeito que a §5 chama de promessa.

O sinal de transição não é uma anotação minha: é **o estado do manifesto**. A sessão 2
começa quando `FX-*`, `FD-*`, `F2C-*` e as cinco `FP-*` da sessão 1 estão `entregue`
com prova no disco, e o que sobra `pendente` por engenharia pertence a `F3-*`, `F4-*`,
`F5-*`, `F6-*` e `F2-ancora-acervo`. `tools/generate-social-tasklist` mostra isso sem
que ninguém precise contar — e o goal **continua aberto** entre as duas, porque a
condição de encerramento da §0-A é o gate terminal, não o fim de uma sessão.

### Onde as 23 entregas de produto entram

Acrescentar entrega ao manifesto sem lhe dar onda é criar trabalho órfão. Cada `FP-*`
tem onda, e as duas que o plano chama de pré-requisito entram **cedo**, não no fim:

| Onda | `FP-*` que entram | Por que ali |
|---|---|---|
| **1** | `FP-medicao-de-humano-real` · `FP-ancora-barata` (probe) | as duas são **medição**, e decidem o resto: uma diz o tamanho do funil, a outra se a âncora pode subir cedo |
| **1'** | `FP-digest-opt-in` | vai junto com o `socialmail`, que é o pacote dele |
| **2''''** (nova, paralela) | `FP-consulta-corpus-publica` · `FP-checagem-de-citacao` · `FP-painel-de-tese` | `internal/consultapublica` é pacote **novo e isolado** — não colide com o domínio nem com o design, e é o que dá conteúdo ao dia 1 |
| **2'''''** (nova, paralela) — **a onda 3 não abre sem ela** | **`FP-gate-tese-nao-caso`** · `FP-quarentena-nao-trava-o-produto` | `internal/oabgate` e `socialpolicy` são pacotes distintos. O gate do art. 42, I entra **antes** de existir a primeira resposta pública — depois seria tarde |
| **3** | `FP-antes-de-perguntar` · `FP-peca-com-fonte-conferida` · `FP-caixa-de-entrada-servidor` · `FP-feed-com-banda-de-temas` · `FP-diversidade-de-respondente` | são handlers e telas: a carroceria |
| **3'** | `FP-convite-para-o-conteudo` · `FP-comentario-de-autoridade` | anti-abuso e papéis |
| **3''** (nova) | `FP-conferencia-de-prazo-do-advogado` · `FP-perfil-que-nao-vira-vitrine` · `FP-util-nao-agrega` | os dois últimos são **testes sobre a página renderizada**, e só existem quando a página existe |
| **4** | `FP-atom-por-tema-e-por-duvida` · `FP-feed-privado-por-capacidade` · `FP-cartao-por-thread` · `FP-exportar-minha-thread` | tudo que é superfície de saída e descoberta |
| **5'** | `FP-agenda-de-prazos-ics` | depende do coletor DJEN da mesma onda |

**A dependência que não pode inverter, e ela é da mesma classe do erro que já corrigi
em `F0-paginas-legais`:** a onda 2 constrói `socialconteudo`, onde nasce a lógica de
publicar resposta; a 2''''' constrói o gate que decide o que pode ser publicado. As duas
são paralelas por pacote — mas se a 2 fechar antes da 2''''', existe caminho de código
que aceita resposta pública sem o detector. Por isso `F2C-handlers` (onda 3) **não abre**
enquanto a 2''''' não estiver verde: a rota HTTP é onde a resposta vira pública, e é ali
que a ausência do gate viraria dano. Vale o mesmo para a allowlist de domínio oficial
que fecha o bypass de `provenanceValid` (§8-a) — **fechar uma porta depois de ela ter
sido usada não a fecha**: o texto já está no índice e no cache da borda.

**A que mais muda de posição em relação ao plano de ontem é `FP-gate-tese-nao-caso`.**
Ele não é refinamento de ética: é pré-condição de a primeira resposta pública existir.
Publicar resposta de advogado antes de o detector existir é rodar o risco que atinge a
inscrição — e uma vez publicado, o texto está no índice, no cache da borda e,
possivelmente, em corpus de treinamento.

**Por que a âncora é a última coisa:** re-data 10.141 páginas com `--ressemear`,
acrescenta segunda diretiva `Sitemap:` no robots e exige purga ampla. Publicá-la
antes de a rota social responder 200 manda o Googlebot para superfície morta — e o
ativo indexado é o que não pode ser posto em risco.

**Mas a âncora pode ser muito mais barata do que isso, e o achado é medido.**
`tools/generate-page-content-revision:309-311` neutraliza, **antes de hashear o HTML
servido**, exatamente dois blocos:
`<section aria-labelledby="conteudos-relacionados">` e `"temas-relacionados"`. Se a
âncora viver **dentro** de um deles, o `served_sha256` não muda — **não há re-datação
nenhuma**, `--ressemear` deixa de importar, e some a razão pela qual a âncora foi
empurrada para a onda 7. O que resta é a purga ampla (que a matriz do contrato já
manda para bloco de relacionados) e a segunda diretiva `Sitemap:` — dois custos
contornáveis, contra a re-datação de dez mil páginas, que é irreversível.

A §13.2 do desenho imaginou a âncora como **link de rodapé**, que é outro lugar do
HTML — é a **posição**, não a âncora, que custa caro. Então `FP-ancora-barata` entra
como probe da onda 1: testar se ela cabe no bloco neutralizado. Se couber, a âncora
sobe cedo e o arranque deixa de esperar a onda 7 (hoje **nenhuma** das 10.141 páginas
linka para `/redesocial/`, e sem a âncora o visitante que chega pelo Google não tem
como saber que a rede social existe). Se não couber, ancora-se **uma área primeiro** —
a menor das 32 —, mede-se 14 dias, e só então se estende.

---

### O schema de `internal/socialconteudo` — a peça maior, desenhada aqui

É a única decisão arquitetural que não delego. Onze tabelas, em `social.db` (mesmo
arquivo de `moderacao`, para que denúncia e conteúdo compartilhem transação):

| Tabela | Papel | A trava que ela carrega |
|---|---|---|
| `perfis` | `conta_id` FK, `handle` único, nome público, bio | **sem** coluna de honorário, preço, nota ou avaliação — `F1-schema-impede-por-ausencia` varre o DDL por esses radicais |
| `perfis_advogado` | inscrição, seccional | linha só nasce quando a verificação é **deferida**; o selo sai de JOIN com a decisão vigente, nunca de coluna de perfil |
| `temas` | `(area, slug)` espelhando as 10.141 rotas | chave é o caminho inteiro — 108 slugs colidem entre áreas (§13.2) |
| `duvidas` | autor, título, corpo, área, `tema_id`, slug, estado | `AvaliarDuvida` roda só `pii` + `publicidadenome` (leigo não é anunciante, §13.3) |
| `respostas` | `duvida_id`, autor, corpo, estado | `AvaliarComentario` roda o `oabgate` completo |
| `fontes_da_resposta` | `resposta_id`, nome, URL, `checked_at` | normalizada **porque** `checkVeracity` é HARD: sem fonte, quase toda resposta de advogado seria bloqueada |
| `follows` | `(seguidor, alvo_tipo, alvo_id)`, `alvo_tipo ∈ {conta,tema,area,duvida}` | assimétrico e **não público** — lista de seguidores de advogado é, funcionalmente, a lista de clientes que o CED art. 42, IV veda. Só a contagem, e ela não ordena nada |
| `posts_blog` | conteúdo autoral | — |
| `reacoes` | curtida | existe e **não entra em ordenação** — o feed é `(banda, data)`, sem score (§13.4) |
| `orcamento_diario` | `(conta_id, dia)`, contadores | **persistido**, não em memória: reiniciar o processo zeraria o limite |
| `quarentena` | início, publicações sobreviventes | 7 dias, 3 posts, sem link externo (§15.4) |

Mais `duvidas_fts` / `respostas_fts` (FTS5 virtual, `F2C-fts5`) — busca dentro do
SQLite social, **sem** um segundo Bleve; o acervo continua sendo consultado por
loopback em `/api/v1/search`.

**Escala — e o contrato é explícito que lentidão em 10k é P0, não otimização.** O feed
de duas bandas precisa saber, por dúvida, se **já existe resposta de alguém
verificado**. Escrito como `JOIN` com `decisoes_oab` a cada requisição, isso degrada
exatamente quando a rede social der certo — e a página é cacheável na borda, o que
esconde o problema até a primeira purga. Por isso a coluna
`respondida_por_verificado_em` é **denormalizada e escrita na mesma transação** que
insere a resposta: a banda vira um predicado sobre uma coluna indexada, não uma
junção. Índices que nascem com o schema, não depois: `duvidas(respondida_por_verificado_em,
criada_em)` para as duas bandas, `respostas(duvida_id, criada_em)` para a thread,
`follows(seguidor, alvo_tipo, alvo_id)` e o inverso para a contagem, `temas(area, slug)`
único. E a paginação é **keyset** (`WHERE criada_em < ?`), nunca `OFFSET` — offset
relê tudo que pulou, e é assim que a página 40 fica mais lenta que a 1.

**Probe curto antes de qualquer passada de escala**, como o contrato manda: semear
10 mil dúvidas sintéticas por *stride* determinístico e medir o feed e a thread antes
de declarar qualquer coisa pronta. Prefixo conveniente não é evidência de escala.

**A consulta do feed é uma só, e é auditável:** banda `aguardando` = sem resposta de
verificado, 30 dias, mais antiga primeiro, ≤10; banda `respondidas` = o resto,
recente primeiro, ≤20 no total. Sem peso, sem decaimento, sem engajamento — o que
torna "resposta em menos de 24 h" consequência mecânica da ordenação, e o que
permite cachear na borda para anônimo e bot com os mesmos bytes.

**O arranque, que é o problema real de toda rede social nova:** no dia 1 não há quem
seguir — mas há **10.141 temas**. Seguir tema é o que dá conteúdo ao feed de quem
não conhece ninguém, e é por isso que `follows.alvo_tipo` é polimórfico desde a
primeira migração, não depois.

**Como `temas` é semeada — e uma premissa minha que estava errada.** Eu havia escrito
que `cmd/social` não pode importar `internal/content` porque `social-isolation`
reprovaria. **Falso, e conferi:** `cmd/social/pagina.go:10` e `superficie.go:12` **já
importam** `internal/content` hoje, e o gate passa — ele proíbe `cmd/server` →
estado social e `cmd/social` → `internal/httpserver` (`socialisolation.go:156-168`),
não `internal/content`. A restrição real é outra e continua valendo: nada do fecho de
`cmd/server` pode tocar `social.db`, `var/social` ou `WIKI_SOCIAL_*`.

A fonte é `data/editorial/published_manifest.jsonl` — **10.141 linhas exatas**,
conferido agora, com `path`, `unique_intent_id` e `title`. A semeadura fica em
`tools/generate-social-temas`, fora do caminho de serving, idempotente por
`(area, slug)` — não por proibição de import, mas porque semear dez mil linhas no boot
de um processo que atende requisição é desenho ruim. `content/pages.json` (78 MB) não
serve: ler 78 MB para pegar caminho é desperdício medido.

**E uma decisão que a refutação cobrou, com razão: onde mora `contas.db`.** FK do
SQLite **não cruza arquivo**, então `perfis.conta_id` referenciando `contas(id)` só
existe se as duas tabelas estiverem no mesmo arquivo. Decido: **`contas` vai para
`var/social/social.db`**, junto de `moderacao` e `socialconteudo`. `contas.Abrir`
aceita caminho arbitrário (`contas.go:162`) e ninguém o chama ainda, então não há
migração a fazer — é escolher agora, antes de existir dado. Consequência que fixo
junto: `socialconteudo` **não abre um segundo `sql.Open`** sobre o mesmo arquivo (seria
outro pool, sem `*sql.Tx` compartilhado); recebe a conexão de `moderacao.Conexao()`
(`moderacao.go:282`), e com ela o mesmo DSN — `busy_timeout`, `foreign_keys`,
`secure_delete`, WAL, `_txlock=immediate`. Um pacote com DSN diferente faria linha
apagada sobreviver nas free pages, e o art. 18, VI viraria ficção.

### Orquestração — como as 122 entregas de engenharia cabem em duas sessões

**O tamanho, estimado por comparação e não por intuição.** Os pacotes existentes dão a
régua: `internal/contas` são 4.746 linhas para 6 tabelas (791/tabela),
`internal/moderacao` 5.434 para 8 (679), `internal/lgpd` 3.680 para 4 (920) — tudo com
teste. Aplicando isso aos **20 pacotes novos** (11 tabelas no domínio mais 19
utilitários): **~24.800 linhas de Go, incluindo testes.** Com ~45 agentes Opus, dá
~550 linhas por agente — volume alto, mas dentro do que um executor competente entrega
com o alvo lido e o contrato no prompt.

**E a refutação corrigiu minha estimativa para cima, com um dado que eu não tinha:** o
melhor dia já medido neste repositório foi **+47.416 linhas de Go** (2026-09-04, por
`git log --numstat`); o segundo, 31.783. Recontando com os handlers das 21 rotas
(~5 k), os 9 gates (~4 k) e as ferramentas (~3 k), o alvo real é **~55–60 mil
linhas** — cerca de **1,3 melhores-dias-de-sempre**, antes de qualquer onda falhar, e
o plano já diz que alguma vai. Somem-se 15+ commits Go serializados no `flock` a
~5 min cada.

**O escopo honesto desta sessão, então, é este:** ondas 0 a 4 — fundação, domínio,
design, carroceria e indexação — **mais as cinco entregas de produto que decidem se o
produto funciona** (`FP-gate-tese-nao-caso`, `FP-quarentena-nao-trava-o-produto`,
`FP-consulta-corpus-publica`, `FP-antes-de-perguntar`, `FP-atom-por-tema-e-por-duvida`).
As ondas 5 a 6' (F3, F4, F5, F6) vão para a sessão seguinte — e não é corte de escopo:
os fechos delas dependem de evento do mundo de qualquer forma (intimação real para duas
OAB, dinheiro entrando, página nascida de thread indexada), então adiantá-las não
antecipa nenhum fechamento.

**O goal não fecha por isso, e é assim que tem de ser.** A §0-A fixa a condição, o gate
terminal é o juiz, e a sessão seguinte retoma pelo prompt da §12 com o que ficou em
`pendente` e a onda registrada — nunca um relatório dizendo "quase pronto". Prometer
122 numa sessão para depois entregar 90 é a mesma falha de declarar o não-feito; dizer
agora quais 90 é o que permite cobrar.

Máquina medida agora: RAM 37% (7/19 GB), swap 7%, load 0,85/8 núcleos. Agente LLM
espera a API, não consome núcleo — o limite é o `flock` do build, não a máquina.

- **Ondas dirigidas, não rajada.** Cada leva nasce do resultado medido da anterior;
  paralelos só em pacotes distintos. Dimensionamento: 6–9 agentes por onda,
  ~45 na sessão. A cardinalidade é minha, nunca do subagente.
- **Eu leio o alvo antes de delegar.** Subagente não herda a conversa: cada prompt
  carrega o arquivo:linha que eu apurei e o trecho do contrato aplicável.
- **Relatório de agente é alegação.** Integro só depois de conferir no disco — diff,
  amostra do dado, exit code. Foi assim que os sete buracos da §1.3 apareceram.
- **Modelos — ordem do dono, 2026-09-05, e ela é restritiva:** **Opus 5 executa a
  maioria das tarefas**. Nada de Sonnet, nada de Haiku, inclusive no que parecer
  mecânico — refatoração, teste, gate. A razão está medida nesta própria sessão: os
  três refinamentos em Opus acharam a audiência que não é gente, os dois deadlocks de
  reputação, o detector do art. 42, I que falta, a âncora barata e o crawler que
  consome 38,6% da origem — nenhum deles é achado de execução, todos são de
  julgamento, e é justamente isso que um modelo menor não faz. Num plano em que o
  risco é a inscrição na OAB e dez mil páginas indexadas, economizar no executor é
  economizar no lugar errado.
  **Fable 5.1 fica para os momentos críticos**, e não se gasta à toa: refutação antes
  do que é caro de reverter — identidade real, âncora do acervo, dinheiro, e a revisão
  final deste plano. Fable chamado para revisar coisa barata é Fable que não estará
  disponível na hora em que derrubar uma premissa custa o projeto.
- **Commit por onda, sob `flock /tmp/opt-wiki-agent-heavy.lock`** — Go dispara build
  de ~5 min; commit por entrega serializaria a sessão inteira no lock.
- **`tools/check-load-headroom --max 12` antes de todo comando pesado**, e o envelope
  `tools/run-heavy-throttled` para suíte global. Agente LLM não consome núcleo, mas
  build e teste consomem — e derrubar o host no meio de uma onda custa mais que
  esperar. Antes de onda pesada, `ai-brief` diz o que já está rodando.
- **Três frases em todo prompt que escreve teste ou fixture:** nenhum dado pessoal
  real em arquivo versionado (com fan-out alto, um CPF plausível derruba
  `sem-dado-pessoal-em-git`) · proibido editar `content/` e `data/` para fazer gate
  passar · nada de stub, mock ou "em breve" — 404 honesto é a regra da casa
  (`rotas.go:44`).

**Três gates do pre-commit que barram onda inteira se ignorados** — li o hook (676
linhas) e estes disparam sozinhos, sem eu pedir:

| Gate | Quando dispara | O que exige no MESMO commit |
|---|---|---|
| `check-sca-govulncheck-evidence` | dependência nova no `go.mod` | rodar `generate-sca-govulncheck-evidence` e commitar a linha nova de evidência. Vale para `yeqown/go-qrcode` (F6) e para qualquer biblioteca que uma onda adote |
| `check-atestacao-grafo-no-commit` | mexer no grafo do validador | reatestar no mesmo commit — senão `ingest-v2-stock` recusa publicar e **nenhum deploy passa** |
| `check-contrato-vs-medicao` | **sempre** | a linha "10.141 páginas públicas" do `CLAUDE.md` tem de bater com a medição (tolerância `max(200, 5%)`). As rotas sociais são dinâmicas e não entram no `published_manifest`, então não deslocam esse número — mas a onda 7 (âncora) toca `public/` e é onde vale conferir |

Some-se a isso o orçamento de tempo do hook, que **acompanha a carga da máquina** por
um fator declarado: com 45 agentes rodando, o commit demora mais por desenho, e
"aumentar o timeout" é explicitamente o que o hook diz não ser a correção.

**Quando uma onda falhar — e alguma vai.** Trabalho de agente **nunca é descartado**:
reorienta-se com o erro medido, retoma-se por `resumeFromRunId` (replay do que já
concluiu custa zero) ou corrige-se a causa raiz antes de re-rodar. Reaproveitar vence
relançar limpo, que vence — nunca — descartar. E a correção é sempre **para frente**:
`git reset`, `checkout`, `revert` e `stash` estão proibidos pelo contrato e barrados
por hook, porque descartam a worktree e apagam o trabalho de sessões concorrentes. Se
uma onda produziu código ruim, o conserto é um commit que o melhora, não um que o
apaga. Onda que falha três vezes no mesmo subsistema não se tenta a quarta: para-se e
ataca-se a família inteira do defeito.

---

## 4. O manifesto não é oráculo — e F4 provou isso

Achado que muda como trato o guardião. `F4-intimacao-multitenant` exige, como prova, o
símbolo literal `"UNIQUE(fonte, corpo_sha256, processo)"` dentro de `internal/djen`. O
schema real usa **quatro** colunas — `UNIQUE(fonte, corpo_sha256, processo,
data_disponibilizacao)` (`dedup.go:66`) — e a data está lá por um defeito medido: o
mesmo despacho-fórmula reaparece **no mesmo processo** meses depois, e sem a data o
segundo seria descartado como duplicata. **O código está mais correto que a prova que
o cobra**, e a prova não casa por substring.

**Não é caso isolado — varri as três famílias de prova e são três casos:**

| Entrega | A prova exige | O disco tem | Veredito |
|---|---|---|---|
| `F4-intimacao-multitenant` | `UNIQUE(fonte, corpo_sha256, processo)` | `UNIQUE(fonte, corpo_sha256, processo, data_disponibilizacao)` (`dedup.go:66`) | código **mais correto** que a prova — a data está lá porque o mesmo despacho-fórmula reaparece no mesmo processo meses depois |
| `F1-sqlite-import-allowlist` | símbolo `sqliteImportAllowed` | `moderncSQLiteImportAllowed` (`policy.go:4249`) — e ela **já autoriza** `cmd/social/`, `socialdb`, `socialconteudo`, `sigilo` | a entrega está feita e **nunca fecharia**: o nome não casa |
| `F1-registros-acesso-cifrados` | pacote `internal/registrosacesso` | `internal/lgpd/registrosacesso.go` — um **arquivo** | `os.Stat` do diretório acusa `pacote_ausente` para sempre |

Nas outras 20 famílias a varredura veio limpa: **zero** entregas marcadas `entregue`
com prova que não casa, e os 22 `pacotes_go` restantes que não existem são exatamente
os pacotes a criar.

Regra que fixo por causa dos dois: quando a prova do manifesto reprovar código que
está certo, **corrige-se a prova**, com o motivo escrito — nunca o código, e nunca
movendo código que funciona só para satisfazer um rótulo. É o inverso de relaxar gate:
relaxar é baixar a régua para o defeito passar; isto é consertar uma régua que mede a
coisa errada. Varri as provas textuais na onda 0 antecipada (§1.4) e as duas acima são
de `simbolos_go` e `pacotes_go` — as duas famílias que a varredura textual não alcança,
e que a onda 0 confere símbolo a símbolo antes de qualquer agente escrever linha.

**O resto do mapa de F4, medido:**

- `internal/djen` **coleta de verdade** — `Cliente.Buscar` (`cliente.go:235`) faz HTTP
  real contra `comunicaapi.pje.jus.br`, e a paginação **não confia no `count`**:
  para só quando a página vem vazia. As fixtures provam o defeito que motivou isso —
  `tjrj_2026-09-03_pagina1.json` declara `count=10000` e traz 5 itens.
- **Mas nada disso roda.** Nenhum `cmd/` importa `internal/djen`; o banco social real
  não tem **nenhuma** tabela `djen_*`; `data/ops/djen_coleta_heartbeat.jsonl` não
  existe; e `systemctl list-timers` (47 timers ativos) não tem **nenhum** de DJEN. É
  biblioteca correta e testada, com zero consumidores. O coletor é o trabalho de F4.
- `internal/prazo` modela **cinco** estados, não os quatro que o próprio comentário
  e o título do manifesto dizem — `EstadoCancelada` entrou depois, com justificativa
  própria. Deriva de comentário, e R1 manda corrigir junto.
- **A trava do DataJud já libera o que F4 precisa:** `policy.go:4309-4312` autoriza
  por prefixo `internal/datajud*` e `cmd/social/`, com comentário antecipando a
  consulta sob demanda. Eu supunha que fosse dependência nova; não é.
- `F4-honestidade-de-cobertura` aponta para `internal/socialrender`, que não existe —
  hoje o render social vive em `cmd/social/render.go`. Como o design (§1.1) já cria
  `internal/socialrender`, a ambiguidade se resolve sozinha: o pacote nasce, e o
  render sai de `cmd/` para ele.

**O corpus que F5 herda — e que hoje ninguém consulta.** Medido: **8.830 artigos de
lei** em 29 diplomas (`data/legal-corpus/`), dos quais 7.770 indexados em
`internal/legalcorpusindex`; **2.384 precedentes qualificados do STJ**
(`data/source-registry/stj_precedentes_qualificados.jsonl`) — e **nenhum código lê
esse arquivo**, só o coletor que o escreve; **1.194 precedentes com tese firmada**;
**754 súmulas**; **65 julgados do Informativo do STF**. O Bleve de `internal/search`
indexa as páginas do site, **nunca** esse corpus, e não existe `cmd/` que exponha
consulta sobre ele — nem para humano, nem para agente. A consulta pública de F5 não é
"expor o que já existe": é construir o primeiro consumidor de um ativo grande que está
parado. É também o item de maior alavancagem do plano inteiro.

**F6, medido:** `internal/pixbrcode` gera payload EMV completo e o CRC está ancorado
no vetor canônico do catálogo CRC RevEng (`0x29B1` para `"123456789"`) — mas o
payload de exemplo usa chave **sintética**, não um exemplo publicado pelo BCB. Falta
só o renderizador de imagem, e `yeqown/go-qrcode` **não está no `go.mod` nem na
allowlist** de `codex2policyenforcement`. `internal/ofx` parseia de verdade (SGML 1.x
e XML 2.x, dedup por `ContaID+FITID`), com fixture sintética construída sobre três
armadilhas reais; o `txid` aparece no `MEMO`, como se espera — mas o próprio código
admite em comentário que **ninguém sabe** se o extrato do banco do dono expõe esse
campo. Daí `F6-extrato-expoe-txid` ser medição, não código: ela decide se a
conciliação usa `PorTxidNoExtrato` (já implementada) ou degrada para valor e data.

**E um desbloqueio de graça:** `F5-decisao-sobre-autoria-de-terceiro` é apenas
registrar em DEC uma verdade que o código já tem —
`structureddata.authorMatchesConfiguredIdentity` (`structured_data.go:1170`) compara
o autor da página por **igualdade exata** contra a identidade única de
`content/site.json`. A maquinaria de autoria do acervo é mono-autor por construção, e
toda decisão da ponte editorial depende de essa premissa estar escrita.

---

## 5. A fronteira de honestidade do "100%"

Esta é a seção mais importante do plano, e a que separa entrega honesta de promessa.

**Li a prova literal de cada `*-fechamento`, e elas não pedem engenharia — pedem
eventos do mundo:** `F2` exige "primeiro conteúdo **de terceiro** publicado"; `F3`,
"primeira conexão **real** registrada"; `F4`, "intimação real chegando para **mais de
uma OAB**"; `F5`, "primeira página nascida da rede social **indexada**"; `F6`,
"primeira cobrança **conciliada**". Nenhuma delas se fecha escrevendo código. E
fabricar o terceiro — criar a conta falsa, o post falso, a cobrança falsa — é
exatamente a fraude que o contrato proíbe em letras maiúsculas.

Por isso o plano entrega **100% da engenharia** e nomeia, item a item, o evento que
falta. Nada é marcado `entregue` sem prova no disco:

| Fecho | A engenharia entrega, testada e provada | O evento que fecha |
|---|---|---|
| `F1-smtp` | fila, transporte por interface, probe de capacidade, DKIM gerado, DNS pronto | entregabilidade medida — a porta 25 é bloqueada pelo provedor |
| `F1-fechamento` | cadastro, sessão, papéis, art. 18, quatro gates de borda verdes | e-mail **chegando** ao Gmail — depende do transporte |
| `F2-fechamento` | dúvida, resposta, feed, moderação, indexação, gêmea, sitemap | uma pessoa real publicando a primeira dúvida |
| `F3-fechamento` | sigilo X25519, mensageria, classificador, push | um cliente real pedindo conexão |
| `F4-fechamento` | coletor DJEN, multi-tenant, prazo, fila DataJud, cache, limitador | intimação real para 2+ OAB inscritas |
| `F5-fechamento` | ponte editorial, consulta pública, consentimento de relicenciamento | o Googlebot indexar a primeira página nascida de thread |
| `F6-fechamento` | Pix BR Code, conciliador OFX, vitrine de cursos | dinheiro entrando e conciliando |
| `F6-segunda-pj-registrada` | minuta do objeto social, DEC redigida, checklist | assinar o ato societário |
| `F2-indexacao` | gêmea Markdown 200, sitemap próprio 200, robots servido anunciando a 2ª diretiva, `/api/v1/redesocial/lote` corrigido e alcançável, `social-cache` e `social-rate-bypass` verdes | o rastreio de bots do acervo voltar acima do teto do tripwire de `social-bots` |
| `F6-extrato-expoe-txid` | parser e conciliador prontos, com fixture do repo | fornecer um extrato real |

**O conjunto mudou em 2026-09-06, e continuam sendo dez — por coincidência de
contagem, não por o conjunto ser o mesmo. A tabela acima é que carrega a verdade.**

`F4-peticao-ao-cnj` **saiu**, e não porque o evento aconteceu: ela foi **suspensa por
perda de objeto**. Ela pedia autorização escrita ao CNJ para a cláusula 3.8 do termo
do DataJud — e a 3.8 não contém a exigência que este repositório lhe atribuía
(conferido no texto oficial V1.2; quem prevê autorização é a 3.13, e só para o teto
de 120 requisições por minuto). Não há evento a aguardar quando o objeto não existe.

`F2-indexacao` **entrou**, por decisão do dono em 2026-09-06. A substância foi
verificada no artefato servido e o quarto elo do título estava defeituoso e foi
corrigido na mesma sessão (`/api/v1/redesocial/lote` respondia 200 no Go e 404 pelo
nginx, por colisão de `location`, e era anunciada em dois descritores). O que a
prende é o tripwire de queda de rastreio do **acervo** dentro de `social-bots` — um
fato do mundo que a rede social não causou: ela recebeu zero requisição de bot em
2026-09-05, e a queda é anterior ao nascimento dela. Reclassificar **não afrouxa
nada**: `social-bots` continua vermelho, o tripwire não foi tocado, e a entrega
continua reprovando o gate terminal, agora com o evento escrito na linha.

Quatro rotas para fazer o gate passar foram examinadas e recusadas como
afrouxamento, e ficam registradas para não serem re-tentadas: (a) invocar a regra
"gate estatístico refutado por medição é pulado", que é a régua de *publicação de
página*, não de prova de entrega; (b) mover o tripwire para gate próprio — quarta
edição do mesmo detector em dois dias; (c) reescrever a prova para não citar
`social-bots`, que mede a coisa certa; (d) dar-lhe um veredito INCONCLUSIVO por
referência instável — refutada por medição própria, porque 2.191 está **abaixo do
piso** (2.202) dos 13 dias de referência, e valor fora do piso é sinal mais forte que
"49,7% abaixo da mediana", não mais fraco.

**São dez, não nove — a refutação achou o que faltava.** `F1-smtp` está `pendente` no
manifesto e **nunca poderá ficar verde**: a prova exige entregabilidade medida, e a
porta 25 é bloqueada pelo provedor, com MX nulo e SPF `-all`. É estrutural, igual às
outras nove, e omiti-la da tabela seria deixar o gate terminal reprovando por um motivo
que o plano não nomeia — que é precisamente o defeito que esta seção existe para
impedir.

**E uma dependência externa que eu tratei como engenharia:** o Resend está autorizado
pelo dono na conversa, mas **não há DEC no disco**, e a lista nominal de exceções do
contrato não o inclui — o `codex2-policy-enforcement` reprovaria o primeiro import como
`external_dependency_unapproved`. A DEC entra no passo 0, **antes** da onda 1'. Idem
para os CNAMEs de DKIM, que só a conta Resend fornece: "SPF/DKIM/DMARC publicados"
depende de um dado que vem de fora, e a onda tem de dizer isso.

**A leitura honesta disso:** ao fim da execução, `check-redesocial-entrega-final`
deve reprovar **apenas** por estes dez, cada um com a linha dizendo qual evento
falta. Todo o resto — os 17 pacotes, os 9 gates, as 21 rotas, o design, os ~180
testes — fecha. Chamo isso de 100% de engenharia, e não de 100% do manifesto, porque
a diferença entre os dois é gente usando o produto, não trabalho meu por fazer.

### `F1-smtp`: a trava é física, medida, e muda o desenho de F1

Eu havia escrito que o MTA próprio era engenharia completa com um risco de reputação.
**Medi, e é pior e mais simples do que isso:**

| Medição minha, agora | Resultado |
|---|---|
| `/dev/tcp/gmail-smtp-in.l.google.com/25` | **BLOQUEADA** |
| `/dev/tcp/mx.uol.com.br/25` (destino fora do Google) | **BLOQUEADA** |
| `/dev/tcp/smtp.gmail.com/587` (controle positivo) | ABERTA |
| PTR de `187.125.5.167` | `1871255167.telemar.net.br` — e esse nome **não tem registro A**: a cadeia FCrDNS quebra no primeiro passo |
| SPF de `wikijuridica.com.br` | `v=spf1 -all` — **nenhum** servidor autorizado |
| DMARC | `p=reject`, sem `rua=` |
| MX | `0 .` — **null MX** (RFC 7505): o domínio declara que não recebe e-mail |

A porta 25 de saída é bloqueada pelo **provedor**, contra três destinos independentes,
com controle positivo em 587. Nenhum pacote, `sudo` ou config em `/opt/wiki` muda
isso — é característica do link, não pendência. E 587 só serve com relay autenticado
de terceiro, que o contrato proíbe (§0.1).

**Armadilha que quase custa um incidente:** `postfix` está em estado `rc` — removido
**com conffiles preservados** — e `/etc/postfix/main.cf` contém a configuração de
`divorcioem1dia.com`, com `relayhost = [smtp.gmail.com]:587` e `sasl_passwd`. Um
`apt install postfix` herdaria isso **em silêncio**: hostname de outro domínio e
relay de terceiro ligado. Qualquer instalação exige `apt purge` antes.

**A rota, decidida por engenharia e não devolvida:**

1. `internal/socialmail` nasce **completo**: fila `email_saida` gravada na mesma
   transação que cria a conta ou o token, templates com `CHECK` de conjunto fechado
   (mala direta impossível de gravar por construção), recuo exponencial — e o
   **transporte por interface**, com a implementação de entrega direta pronta.
2. Um probe grava a capacidade real em `data/ops/social_email_entregabilidade.jsonl`:
   porta 25 alcançável, FCrDNS fechando, `Authentication-Results`. Hoje ele grava
   "bloqueado pelo provedor" **com a evidência** — isso é dado real, não desculpa.
3. **O produto deixa de ficar refém do e-mail — mas `F1-smtp` e `F1-fechamento`
   continuam `pendente`.** A distinção importa: a prova de `F1-fechamento` diz
   literalmente "e-mail de verificação **chegando** ao Gmail". Reescrever essa prova
   para ela passar seria relaxar o gate, que a §5 do contrato chama de fraude
   operacional — e a medição boa não compra o direito de fazer isso. Os dois IDs ficam
   pendentes, com a medição como evidência, e nasce `F1-socialmail-ate-a-fronteira`,
   esse sim `entregue`.
   O que muda no **produto**: e-mail confirmado vira **promoção de reputação**, não
   portão — a mesma lógica que §15.4 já aplica à prova de trabalho ("só levanta
   limite, nunca é portão"). O estado `nao_confirmada` **não é removido**
   (`entrada.go:301` continua como está): ganha um **tier**. Conta não confirmada lê,
   posta menos por dia, sem link externo e sem mensagem direta; `ativa` entra na
   quarentena normal. No dia em que o transporte existir, a promoção só automatiza.
3-bis. **Dois buracos que o pivô abre, e que fecho junto** — senão troco um defeito
   por outro:
   - **Senha esquecida seria conta perdida para sempre.** Nasce
     `FX-codigos-de-recuperacao`: códigos de uso único emitidos no cadastro, exibidos
     uma vez, gravados só como hash Argon2id, em tabela nova no schema de `contas`.
     É a prática consagrada de códigos de backup de 2FA, é self-hosted por natureza e
     não depende de canal nenhum.
   - **O modo "sob ataque" fica inerte.** `GerarOTP`/`ConcluirEntradaComOTP`
     (`entrada.go:351,372`) mandam OTP por e-mail; sem transporte, a defesa contra
     credential stuffing degrada para backoff apenas. Digo isso em vez de esconder —
     e os mesmos códigos de recuperação servem de segundo fator no modo sob ataque,
     o que fecha os dois com uma tabela só.
4. O **canal do titular (art. 18) não vira e-mail**: é formulário autenticado no
   próprio site, com trilha — que é mais forte que e-mail para provar atendimento, e
   não depende de MX (que hoje é null por decisão de higiene).
5. **SPF, DKIM e DMARC passam a ser publicados por automação** — o dono autorizou, em
   2026-09-05, usar a Global API Key e o e-mail que já estão em `.env.local` para
   criar o token que faltar. Isso tira o DNS da lista de travas.
   **Como faço, com o menor privilégio:** a Global API Key abre a conta **inteira**, e
   usá-la no dia a dia é guardar uma chave-mestra num script. Ela é usada **uma vez**,
   por `tools/generate-cloudflare-token`, para criar um token de escopo mínimo —
   `DNS:Edit` restrito à zona `wikijuridica.com.br` —, que passa a viver em
   `.env.local` como `CLOUDFLARE_DNS_EDIT_TOKEN` e é o único usado dali em diante.
   `tools/generate-dns-record` (nova, seguindo o padrão de `curl` já documentado em
   `ops/cloudflare/dns-aid.md`) aplica os registros e grava o antes/depois em ledger,
   porque mudança de DNS sem trilha é mudança que ninguém consegue desfazer.
   **O que ainda não publico, e o motivo:** um `ip4:` apontando para o IP desta
   máquina seria declarar autorização falsa — ela não entrega. O SPF nasce autorizando
   o **Resend**, que é quem de fato envia, e aí `v=spf1 include:... -all` passa a ser
   uma afirmação verdadeira em vez de contraditória.

### O que é próprio foi esgotado — e o que sobra, com a oferta do dono

O dono ofereceu o Resend e pediu, corretamente, para eu ver **o que for próprio
primeiro**. Esgotei, e digo o resultado sem rodeio:

| Rota própria | Veredito |
|---|---|
| Porta 25 por IPv4 | **morta** — bloqueio do provedor, medido contra 3 destinos |
| Porta 25 por IPv6 | **morta** — o IPv6 do host não tem PTR, e o Gmail rejeita remetente IPv6 sem PTR na origem |
| Cloudflare Tunnel (já autorizado) | **não serve** — faz ingress, não entrega SMTP de saída |
| MTA em outro host | funciona, mas é **infraestrutura nova** (VPS): custo e decisão do dono |
| Não depender de e-mail | **funciona, e é a que adoto** — o tier de conta e os códigos de recuperação acima |

O ponto duro é lógico, não de esforço: **provar posse de um endereço de e-mail exige
enviar e-mail**. Não há substituto próprio para essa função específica. O que é
próprio é **o produto não ficar refém dela** — e isso está desenhado acima.

**Decisão, então:** o transporte fica atrás de uma interface com **duas implementações
reais** — entrega direta por MTA (correta, pronta, inerte nesta máquina) e o
**Resend**, que o dono autorizou nominalmente. O Resend entra como **exceção nominal
datada de 2026-09-05**, registrada em DEC no mesmo formato da Google Indexing API, e
com três limites que o mantêm fora do caminho crítico:

1. **O produto funciona sem ele.** Se a chave sumir ou o serviço cair, a fila
   `email_saida` acumula, ninguém vê erro, e as contas seguem no tier não confirmado.
   É melhoria de experiência, não dependência.
2. **Nenhum dado do projeto trafega além do necessário:** destinatário e um template
   de conjunto fechado. Sem corpo livre — a função que aceitaria corpo arbitrário não
   existe no pacote, por construção.
3. **A chave mora em `.env.local`** (fora do versionamento, já é o padrão da unit via
   `EnvironmentFile=-`), nunca no repo, nunca em prompt de agente.

E o SPF passa a autorizar o Resend em vez de um IP que não entrega — o que torna o
`v=spf1 -all` atual uma declaração verdadeira em vez de contraditória.

**O que continua do lado do dono, em uma linha:** a chave do Resend, que ele já
ofereceu — e, se um dia quiser entrega 100% própria, um host com porta 25 liberada e
PTR configurável. O DNS **saiu** dessa lista: com a autorização de usar a Global API
Key para emitir um token de escopo mínimo, publicar SPF, DKIM e DMARC virou
engenharia, não pedido.

---

## 6. O que a refutação adversarial derrubou — e as contradições do plano original

Rodei uma passada adversarial (`model: fable`) contra este dossiê e conferi cada
achado no disco. Cinco erros meus já estão corrigidos acima (o caminho
`/assets/css/`, o "bloqueado por infra", o "drift impossível", a borda por superfície,
o import de `internal/content`). Restam **cinco contradições no plano de origem** que
nenhuma onda resolveria sozinha — cada uma entrega código que ninguém usa ou põe um
gate vermelho:

| Contradição | O choque | Resolução que adoto |
|---|---|---|
| `F2-sse-com-teto` | SSE exige `EventSource`, que é JavaScript — e a CSP social é `script-src 'none'` nas **duas** variantes, com as telas desenhadas sem JS. O endpoint não teria cliente | Atualização por PRG e recarga. O ID **não some**: vira `suspenso` no manifesto, com o motivo e a condição de volta (haver JS, com hash na CSP e ADR) |
| `F2-avatar-reencodado` | Pede pipeline de re-encode enquanto §13.6 decide **sem avatar** (iniciais em `<span>`, e é o que economiza 1,4 KB/tela e dispensa `img-src`) | Mantenho **sem avatar**. O ID vira `suspenso` com o motivo — implementar re-encode para uma tela que não exibe imagem seria código morto |
| `F2-canal-de-maquina-social` | Pede `internal/httpserver` (fecho do `cmd/server`) abrindo `social.db` em `mode=ro` — e `socialisolation.go:119-152` reprova qualquer pacote desse fecho que **referencie** `social.db`/`var/social`/`WIKI_SOCIAL_*` | O canal de máquina lê a rede social **por loopback HTTP** (8091), nunca pelo arquivo — ver o desenho logo abaixo. Preserva o gate sem afrouxá-lo; a pressão para afrouxar seria R10 |

**Como o canal de máquina alcança a rede social — e aqui eu contradisse o desenho
aprovado.** Eu propus **loopback HTTP** para o `cmd/server` ler a rede social sem tocar
o arquivo. Fui à §11.7 e ela **rejeita isso nominalmente**: *"Proxy por loopback
recriaria o acoplamento que o processo separado comprou"*, e decide `?mode=ro` sobre o
SQLite, com fail-open por capacidade armada (`mcp.go:341-349` — a ferramenta só é
registrada quando as dependências existem, para não anunciar em `tools/list` o que
toda chamada recusaria). Com loopback, `cmd/social` caído faz o MCP anunciar ferramenta
que sempre falha — exatamente o defeito que aquele padrão existe para impedir. E o
CLAUDE.md §7 exige que os quatro canais rendam o **mesmo objeto**, não bytes de outro
processo.

**Então a resolução não é escolher entre desenho e gate: é o gate aprender a
distinguir.** `socialisolation` reprova qualquer referência a `social.db` no fecho do
`cmd/server` — regra certa contra o dano certo (o acervo depender da rede social para
subir). Mas **abertura somente-leitura com capacidade armada não é esse dano**: o
`cmd/server` sobe, serve as 10.141 páginas e o canal de máquina inteiro com o arquivo
social ausente; o que muda é uma ferramenta a menos em `tools/list`. O gate ganha a
distinção — leitura `?mode=ro` com fail-open é permitida e **testada**; escrita,
dependência de boot ou import de pacote social continuam reprovando. É a política do
repositório sendo corrigida na camada certa, com teste, não contornada.

`internal/agentsurface` continua sendo a fonte única, e a rede social entra ali como
serviço anunciado. E o inverso do isolamento se preserva intacto: `cmd/social` **não**
pode importar `internal/httpserver` (`socialisolation.go:156-168`).
| `F0-paginas-legais` na onda 1'' | §15.3 e o próprio manifesto mandam reescrever o aviso **depois** de o código existir; a prova cita "mensagem removida pelo autor", que é comportamento de `F1-direitos-do-titular` | **Move para a onda 3**, depois dos direitos do titular. É o defeito que `promessa-privacidade-tem-substrato` existe para impedir |
| Diretiva `Sitemap:` na onda 7 | `additional_sitemap_paths` aplicado antes de `/redesocial/sitemap.xml` existir aponta o robots para um 404 | Vai junto com `F2-sitemap-social-fora-do-indice`, na **onda 4**, e não antes |

**Nenhuma entrega é apagada** — a ordem do dono é que nada seja descartado. Conferi
como o guardião trata isso: `EstadosConhecidos` é uma lista **fechada**
(`completude.go:46`) de `entregue` e `pendente`, e estado fora dela reprova
(`:257`) — o que é a proteção certa contra estado inventado com erro de grafia. E já
existe um campo `Motivo` (`:122`), escrito para "registrar por que uma entrega nasceu
pendente quando isso foi uma decisão".

Então acrescento **`suspenso`** à lista, com duas travas: só é aceito **com `Motivo`
não-vazio**, e o `entrega-final` o relata separadamente em vez de bloquear. Sem a
exigência do motivo, `suspenso` viraria porta dos fundos para esvaziar escopo — que é
o oposto do que o dono pediu.

Mais dois itens que estavam fora de qualquer onda e agora entram:
**`P0-molde-stf-informativo`** (pendente, não-social — `check-redesocial-entrega-final`
não fica verde sem ele) vai para a onda 0; e o **WhatsApp de `F3-notificacao-sem-conteudo`**
depende de `whatsmeow`, dependência de runtime nova que exige ADR com licença, versão
fixada e benchmark — e um número pareado por QR, com risco de ban. Desenho a
notificação **atrás de interface**, entrego o canal interno (que não depende de
terceiro nenhum), e o WhatsApp fica como implementação plugável com o ADR redigido.

---

## 7. O guardião — cinco melhorias, e o que não se toca

Li `internal/redesocialcompletude/completude.go` inteiro antes de propor qualquer
coisa, e o registro honesto é que **ele é melhor do que eu supunha**. Já detecta 31
classes de defeito, e três delas são de desenho raro: `redesocial_prova_stub` varre a
AST atrás de stub estrutural (`stubsEstruturaisEm`, `:684`); `corpoAsserta` (`:941`)
só conta como teste a função que **realmente asserta**, não a que compila; e
`CoberturaDeTeste` é **adaptativa** — exige `ceil(exportadas × cobertura)`, de modo
que a régua acompanha o pacote sozinha, com o comentário explicando que número fixo
"é como um gate ensina a ser afrouxado". Nada disso se reescreve.

O que falta são cinco coisas, e quatro nasceram de defeitos que esta investigação
encontrou:

| Melhoria | Por que, com o caso concreto |
|---|---|
| **`suspenso` + `Motivo` obrigatório** | `EstadosConhecidos` (`:46`) é fechado em `entregue`/`pendente`. Sem um terceiro estado, resolver uma contradição do plano (SSE sem JS, avatar sem avatar) só teria duas saídas: implementar código morto ou apagar a entrega. As duas são piores. `suspenso` sem `Motivo` reprova — senão vira porta dos fundos |
| **Distinguir prova errada de trabalho a fazer** | Hoje `redesocial_prova_texto_ausente` trata igual "o arquivo ainda não existe" e "o arquivo existe e o texto mudou". Foi o caso de `F4-intimacao-multitenant`, cuja prova cobra `UNIQUE(fonte, corpo_sha256, processo)` enquanto o código tem a versão correta com quatro colunas. Quando o arquivo existe e um prefixo do texto casa, o achado vira **`redesocial_prova_possivelmente_desatualizada`**, com a linha do disco ao lado da esperada |
| **Campo `depende_de_evento_externo`** | Seis `*-fechamento` esperam usuário real, bot real ou dinheiro real (§5). Hoje eles ficam `pendente` para sempre e o `entrega-final` nunca fica verde — e gate permanentemente vermelho é gate que ninguém lê, o que a DEC-045 já reconhece. Com o campo, o relatório separa "falta engenharia" de "falta acontecer", e o verde volta a significar algo |
| **Prova de rota** | O guardião conhece pacote, símbolo, arquivo, texto e gate — e **nada** sobre HTTP. Numa entrega de 21 rotas, isso é o furo maior: `FD-tela-feed` pode passar com o pacote existindo e a rota devolvendo 404. Campo `rotas`: cada caminho está registrado no mux **e** responde o status esperado numa sonda com UA próprio |
| **Gate citado tem de PASSAR, não só existir** | Hoje `confereProva` verifica que o gate está em `Names` e tem `case` no dispatcher — **por texto**, sem executá-lo. Uma entrega `entregue` pode citar um gate que está vermelho agora, e o guardião não vê. É a diferença entre "o instrumento existe" e "o instrumento aprova". Como executar todo gate de toda entrega a cada commit seria caro, a execução vale só no `entrega-final` — que é o gate de declarar pronto, roda uma vez e pode pagar |

As duas primeiras entram na onda 0, porque o aditivo do manifesto depende delas. A
prova de rota entra na onda 2'', junto com as telas — antes não há rota para provar. E
a execução de gate citado entra na onda 8, no fechamento, que é quando ela é usada.

**O que fica sem prova, dito em vez de escondido:** um acoplamento acervo↔social que
passe o caminho do banco por parâmetro, sem literal de marcador no arquivo, escapa da
varredura de `socialisolation` — e não achei desenho barato para isso sem falso
positivo alto (exigiria taint tracking). Fica registrado como limite conhecido, não
como cobertura.

---

## 8. Por que ela não morre de sala vazia — e as métricas que provam isso

Rede social nova morre por uma causa dominante: ninguém posta porque não há ninguém.
Este projeto tem a única vantagem que resolve isso, e ela é intransferível:

- **A audiência existe — mas o número que eu usava não é gente, e isso muda o
  produto.** Eu escrevia "1.285 visitantes únicos por dia" a partir de
  `edge_traffic_daily.jsonl`. Fui ao campo e ele **se autodenuncia**:
  `"uniques_filter": "none_includes_self_traffic"` — inclui bot e inclui o
  aquecimento da própria borda, que já foi medido como 93% do tráfego de borda. E hoje
  o valor é **3.240**, não 1.285. Não é contagem de pessoas por definição do próprio
  registro.
  Os dois instrumentos que medem humano dizem outra ordem de grandeza: o **Clarity**
  (janela de 3 dias) vinha de 44 sessões humanas na coleta de 01-09 a 106 na de 04-09
  — de ~15 para ~35 por dia, subindo de forma consistente; o **log de origem**, sem
  bot e só `route_class ∈ {page, markdown}` com status 200, dá ~150 pageviews e ~100
  IPs distintos por dia. Os dois são **pisos**: o Clarity só carrega após 1,2 s de
  ocioso e morre com bloqueador; o log de origem não vê quem foi servido pela borda
  com `s-maxage=604800`, que é a maioria.
  **E uma trava que só aparece quando se junta as duas pontas:** a CSP da rede social
  é `script-src 'none'` nas duas variantes — logo **não haverá Clarity nem GA4 em
  `/redesocial/`**. O instrumento que hoje mede humano no acervo **não mede a rede
  social**, por decisão de segurança que está certa e não se afrouxa. A medição da
  audiência social sai do **log de origem**, e por isso `FP-medicao-de-humano-real`
  tem de nascer sabendo disso — senão publica um piso que, para a superfície nova, é
  estruturalmente zero.
  **O que os instrumentos autorizam dizer:** entre ~35 e ~150 pessoas por dia, teto
  não medido, tendência de alta. É audiência real e é o funil certo — converter quem
  já está na página com a dúvida na cabeça —, mas é uma ordem de grandeza menor do que
  o plano supunha, e toda aritmética de funil abaixo parte dela. Nasce
  `FP-medicao-de-humano-real`: uma série que reconcilia os três instrumentos e publica
  **piso, método e a ausência de teto**, nunca um número único. R3 do contrato: amostra
  não se apresenta como população.
- **A sala tem 10.141 cômodos — mas ainda sem porta, e isso muda o sequenciamento.**
  A promessa é que quem cai em `/familia/divorcio-consensual/` pelo Google encontre a
  discussão daquele tema ali. **No dia da abertura isso é falso:** a âncora é a onda 7,
  e hoje **nenhuma** das 10.141 páginas linka para `/redesocial/`. Ou a âncora barata
  funciona (o teste do bloco neutralizado, §3), ou o que o visitante vê na primeira
  semana precisa se sustentar **sozinho** — e é por isso que `FP-consulta-corpus-publica`
  deixa de ser bônus e vira pré-requisito do arranque.
- **O advogado volta pela ferramenta, não pela promessa de caso.** Prometer caso sem
  ter caso queima a base no primeiro mês. O gancho é o **painel de prazos do DJEN** —
  dor diária que hoje custa assinatura no mercado. Por isso F4 não é "fase tardia":
  é retenção.
- **Distribuição que não se compra:** sendo a única rede social jurídica legível por
  agente (MCP, A2A, gêmea Markdown), ela vira a fonte que os assistentes citam.

### DEC — a rede social não carrega analytics de cliente, e isso não é desativar a medição

Duas regras do mesmo contrato apontavam para lados opostos sobre a **mesma** superfície,
e um agente obedeceria a que lesse primeiro. Decido agora, com o motivo, porque
ambiguidade de uma linha com um ramo fatal é o que a §8(b) já mostrou custar caro.

**A colisão:** o CLAUDE.md §6 diz que "analytics é PERMITIDO (decisão do dono,
2026-08-27) e desativar a medição é proibido". A CSP da rede social é
`script-src 'none'` nas **duas** variantes — logo zero GA4 e zero Clarity em
`/redesocial/`.

**A decisão: `script-src 'none'` fica, e a medição da rede social é 100% de servidor.**
Três razões medidas, não preferência:

1. **A ordem de 2026-08-27 foi sobre o acervo, e a topologia lá é o oposto.** As
   10.141 páginas saem estáticas de `public/` com `s-maxage=604800` — a borda serve a
   maioria dos visitantes e o log de origem **não os vê**. Sem GA4 e Clarity ali não
   haveria medição de humano nenhuma, e é por isso que a ordem existe. Na rede social
   **toda** requisição atravessa o Go (não há `public/`), e o
   `proxy_cache_bypass $cookie_wjsession` garante que o logado sempre chegue à origem.
   O instrumento de servidor vê o que o de cliente veria, e mais: o Clarity só carrega
   após 1,2 s de ocioso e morre com bloqueador — é piso, e o próprio plano já o trata
   assim (§8).
2. **A rede social publica texto de terceiro.** `script-src 'none'` é a defesa que
   segura o payload **quando a sanitização falhar** — e a sanitização é código meu
   (`FX-sanitizacao-de-ugc`, §9.8), logo é código que pode ter defeito. Trocar a única
   proteção que não depende de eu estar certo por um número que já tenho de outra
   fonte é trocar para pior.
3. **Um `<script>` a mais reprova oito gates.** `htmlcontract.go:189` isenta
   `internal/pageinline.Script` byte a byte, sem atributo, e a CSP do acervo deriva o
   hash **dessa** constante. Servir o loader do acervo em `/redesocial/` exigiria ou um
   segundo hash na CSP social, ou `'unsafe-inline'` — e o contrato proíbe o segundo.

**As três obrigações que essa decisão carrega, e sem as quais ela vira desculpa:**

- `FP-medicao-de-humano-real` publica, **para a rede social**, a série derivada do log
  de origem com as dimensões que o GA4 mede no acervo — sessão, rota, origem de
  referência —, com o método escrito e o piso declarado (R3: amostra não se apresenta
  como população).
- Essa série nasce **junto com a primeira rota pública nova**, nunca depois. "Não tem
  analytics" só é honesto enquanto "tem medição"; sem a série, isto seria exatamente o
  que a ordem do dono proíbe.
- Um gate prova que `pageinline.Script` **não** aparece em nenhuma resposta de
  `/redesocial/` — senão, no dia em que alguém copiar o `<head>` do acervo para cá, a
  CSP bloqueia a folha e a rede social fica sem estilo, em silêncio.

Se um dia a rede social precisar de JS (o `F2-sse-com-teto` suspenso é o caso natural),
o caminho é ADR com hash na CSP, nunca `'unsafe-inline'` nem `'self'` — e esta DEC é
que fica registrada como o ponto de partida a revisar.

**Métricas desde o dia 1**, todas já instrumentáveis: leitor→cadastro,
cadastro→primeira postagem, verificados ativos por semana, threads respondidas em
menos de 24 h, páginas do acervo nascidas de thread. Nenhuma é vaidade — e a de 24 h
é **consequência mecânica** da ordenação do feed, não esperança.

### Dois deadlocks na política vigente — o produto não funcionaria no dia 1

Achados por leitura cruzada de `content/social_policy.json` com a §13.3 do desenho, e
os dois são de configuração, não de arquitetura:

**(a) Eu diagnostiquei ao contrário, e a refutação me corrigiu.** Escrevi que a
quarentena (`link_externo_permitido: false`) colidiria com a `fonte_url` obrigatória e
travaria o advogado por sete dias. **Não trava — porque nenhuma das duas pontas existe
em código:** `fonte_url` aparece **uma vez** no repositório, num comentário
(`oabgate/campos.go:56`), e `link_externo_permitido` tem **zero** enforcement (só
validação de política e a página de transparência). A proveniência entra por parâmetro
separado, que nenhum detector de link varre.

**O defeito real é o oposto, e é pior: um bypass.** Li `provenanceValid`
(`oabgate.go:633`) e ele aceita **qualquer** `SourceURL` não vazia com `CheckedAt` não
vazio. Ou seja: `https://example.com` + uma data satisfaz o gate HARD de veracidade do
Provimento 205. A allowlist de domínio oficial que eu propunha continua sendo a
entrega certa — mas para **fechar uma porta**, não para destravar uma trava. Rotular
errado o defeito me fez sequenciá-lo como "configuração"; ele é **segurança de gate**,
e entra antes da primeira resposta pública.

**(b) `destrava_abrir_thread: 20` sobre `reputacao.inicial: 0` pode travar o leigo para
sempre.** A expressão "abrir thread" aparece **uma vez** em todo o `PLANO_REDE_SOCIAL`
e não é definida em lugar nenhum. Se "thread" for a dúvida — e a rota é
`/redesocial/duvida/{slug}/` —, então nenhum leigo novo pode perguntar, nunca: os
únicos ganhos de reputação (`post_sobrevive_30_dias: 1`, `resposta_marcada_util: 3`)
exigem ter publicado antes. A rede social nasceria sem o ato que a define.

**A correção, que não afrouxa nada:** `fonte_url` passa a ser campo de **vocabulário
fechado de domínio oficial** (planalto, lexml, `*.jus.br`, in.gov.br) e por isso **não
conta como link externo** para a quarentena — a quarentena continua barrando link
arbitrário, que é a superfície de spam que ela existe para barrar. E `fonte_url` livre
seria, aliás, o vetor de spam mais valioso da plataforma entrando pela porta que a
própria regra de ética abriu. Quanto a (b): abrir dúvida **nunca** depende de
reputação, e o termo ganha significado escrito e testado no `social_policy.json`, com
trilha datada — ambiguidade de uma linha com um ramo fatal é exatamente o que a trilha
existe para impedir.

### O detector que falta, e é o único risco que encerra o projeto

`internal/oabgate` roda 14 regras do Prov. 205 — superlativo, preço, porte,
promessa de resultado, CTA, veracidade. **Nenhuma detecta aconselhamento em segunda
pessoa sobre caso concreto.** Varri `oabgate`, `legalmarketingpolicy`, `moderacao` e
`publicidadenome` por `art. 42|42, I|aconselhamento|caso concreto`: zero.

A §1.3 do desenho chama o art. 42, I de "a regra mais dura do produto" e fixa a
fronteira **tese × caso concreto** — e essa fronteira existe hoje só em prosa. O
primeiro advogado a responder em público é o dono, sob OAB/RJ 227191, e "responder
consulta com habitualidade em meio de comunicação social" é exatamente o que a
plataforma vai fazê-lo fazer dez vezes por dia. É a única classe de risco que **encerra**
o projeto em vez de atrasá-lo, porque atinge a inscrição.

**Mas o detector léxico que eu havia proposto é inviável, e a refutação provou com o
próprio acervo.** Eu ia acusar "no seu caso", "você deve", "entrar com [ação]". Medi
sobre as 10.141 páginas publicadas: **1.473 (14,5%) usam "você"** e **94 (0,9%) casam
os gatilhos** — páginas que a própria casa publica sob OAB/RJ 227191. Três exemplos
reais que o detector reprovaria:

> "A ideia por trás disso é simples: **você deve** receber com folga, para poder
> efetivamente aproveitar o descanso" (`trab-pagamento-ferias-prazo`)
> · "exige **entrar com uma ação** que pode levar meses"
> (`tra-acordo-ou-processo-acidente-transito`) · "ser fundamentada em tese não
> significa ser devida **no seu caso**" (`tra-regresso-seguradora-cobra-terceiro-culpado`)

E há um erro de mira mais fundo: o art. 42, I proíbe **responder com habitualidade a
consulta** em meio de comunicação social. O ilícito é **frequência × formato**, não a
locução. Um regex mira a palavra e erra o delito.

**O desenho correto, então, tem três peças e nenhuma é léxica:**

1. **Classificação estrutural no formulário.** O advogado escolhe, antes de escrever,
   entre "comentário sobre o tema" e "orientação a quem perguntou" — e a segunda vai
   para o canal privado **por construção**, sem NLP e sem falso positivo. É a fronteira
   da §1.3 virando campo, não adivinhação.
2. **Teto medido de respostas públicas por advogado por semana**, registrado na trilha.
   É o que ataca a habitualidade, que é o que a norma nomeia — e é o mecanismo que
   `FP-diversidade-de-respondente` já insinuava sem assumir.
3. **O léxico entra só como aviso pré-publicação**, nunca HARD, e nasce com o teste de
   falso positivo rodando sobre essas 94 páginas: se ele as reprovar, é ele que está
   errado. Este repositório já teve detector que acusou 46 páginas e as 46 eram falso
   positivo — a lição está paga.

Some-se a amostragem datada de moderação sobre as respostas do dono, que é o registro
que elide presunção. `FP-gate-tese-nao-caso` continua sendo a entrega mais importante
da camada de produto; o que muda é que ela deixa de ser um regex e vira um desenho.

**Uma entrega que a refutação reescopou, e o motivo vale para as próximas.** Eu havia
proposto `FP-triagem-de-prazo-do-leigo` — "recebi a intimação em tal dia, até quando
ajo" — porque `internal/prazo` está pronto e sem consumidor. **Medi o pacote e ele não
faz isso:** `prazo.Entrada` (`prazo.go:14`) pede `CodigoClasse`, `NomeClasse`,
`TipoDocumento` e `TipoComunicacao`, que vêm de `EntradaDoDJEN(djen.Comunicacao)`; e as
presunções (`presuncao.go`) são atos do **diário eletrônico** — sentença e acórdão com
embargos em 5 dias pelo CPC art. 1.023 —, contados no calendário forense. O leigo
intimado pessoalmente não tem nenhum desses campos, e o termo inicial dele é outro
(CPC art. 231).

E há a razão que decide antes da técnica: dizer a um leigo até quando ele deve agir é
**consultoria jurídica**, reservada à advocacia pelo art. 1º, II da Lei 8.906/94 — uma
plataforma que a automatiza pratica, sem advogado no circuito, o que a lei reserva.
Então a entrega **não é suspensa** (o código está pronto e o valor é real): ela é
reescopada para `FP-conferencia-de-prazo-do-advogado`, ferramenta profissional para
profissional verificado, que é o gancho de retenção que a §8 já identificou.
Para o leigo fica o que é lícito e continua útil, e já está em outras entregas: dizer
que **existe** prazo e que ele precisa de advogado — informação, não cálculo.

**A trava anti-abuso que decide o resto:** a página funciona sem JavaScript, logo
prova de trabalho só pode **levantar** limite, nunca ser portão — portão de PoW é
falha de acessibilidade e de visibilidade para bot ao mesmo tempo. Quarentena,
orçamento diário persistido, reputação que nunca vira ranking público (Prov. 205
art. 5º), tempo mínimo com HMAC e erro legível, e conta inautêntica **nunca**
suspensa automaticamente: sai uma linha de fila por cluster, com evidência, para um
humano — é o registro datado de ter olhado que elide a presunção da tese 3 do STF.

---

## 9. As lacunas de engenharia que o refinamento achou

Nove achados que faltavam ao plano, todos com evidência no disco. Ordenados por dano.

**9.1 — Não existe invalidação de cache na escrita: publica-se e ninguém vê por uma
hora.** `cacheControlPublico = "public, max-age=600, s-maxage=3600"`
(`rotas.go:25`), e a regra da Cloudflare usa `edge_ttl: respect_origin` — logo a borda
guarda **uma hora**, não os 10 min do nginx. E `grep redesocial` em
`purge-edge-cache`, `warm-edge-cache`, `warm-origin-cache` e `deploy-publico` devolve
**zero nas quatro**. O defeito é cruel porque se esconde de quem testa: o
`proxy_cache_bypass $cookie_wjsession` faz o autor ver o próprio post. Quem não vê é
todo o resto do mundo — e a métrica "respondida em menos de 24 h" mente por uma hora.
`FX-invalidacao-na-escrita`: `internal/socialpurga` calcula as rotas afetadas por uma
dúvida ou resposta e as invalida na origem e na borda, com teste de mutação que remove
a chamada e prova que a rota anônima continua servindo o corpo anterior.

**9.2 — A cadeia OOM → laço → silêncio, com quatro elos ausentes.** `SetMaxOpenConns`
**não existe em produção** (só num teste), então o pool é ilimitado e cada conexão do
modernc carrega cache próprio; a unit documenta que a folga real sob `GOMEMLIMIT=600MiB`
depois do pico de Argon2 é de **88 MiB**; `Restart=always` com `StartLimitIntervalSec=0`
é laço sem teto; e **nenhuma das duas units tem `OnFailure=`**. Somado ao §1.4(b-bis) —
nenhum vigia olha o 8091 —, a rede social pode entrar em laço de restart e nada avisa.
`FX-pool-drenagem-e-vigia`. Detalhe fino a corrigir junto: `esperaDeDrenagem` é 10 s
contra `WriteTimeout` de 30 s, então uma requisição em voo aos 12 s é cortada no meio
do corpo, depois de o cliente já ter recebido 200.

**9.3 — Zero `ALTER TABLE` no repositório, e onze tabelas chegando.**
`CREATE TABLE IF NOT EXISTS` **não altera tabela existente**: o dia em que `duvidas`
precisar de uma coluna, o binário novo sobe contra o schema velho, o `CREATE` é um
no-op silencioso, e o defeito aparece no primeiro `INSERT` **em produção** — com o
`Restart=always` transformando-o em laço. `FX-schema-versionado` grava a versão;
falta o que **fazer** quando ela divergir. `FX-migracao-versionada` entra na onda 1,
**antes** de `F2C-schema`, com `ErrVersaoAdiante` para o caso que mata em silêncio:
banco escrito por binário mais novo que o que está subindo, num rollback de deploy.

**9.4 — A colisão mais cara da sessão, e ela passa em todo gate.** A entrega da onda 1
é "concentrar o DSN e os pragmas em `internal/socialdb`, de onde `contas`, `moderacao`
e `socialconteudo` importam a mesma string". Um executor que leia isso e **uniformize
os três** destrói a garantia do art. 18, VI — porque `lgpd.db` usa
`journal_mode=DELETE` **de propósito** (`banco.go:60-72`): em WAL o `secure_delete` só
se completa no checkpoint, e há teste que mede os bytes. **Nenhum detector do
repositório compara journal mode contra finalidade**, então a regressão seria verde.
Vai literalmente no prompt do agente da onda 1, com o arquivo e a linha.

**9.5 — Manada na borda depois da purga que o próprio plano manda.** As locations
dinâmicas do acervo (`@markdown`, `@fallback`) têm as quatro proteções:
`proxy_cache_key` explícita, `proxy_cache_lock`, `proxy_cache_background_update` e
`lock_timeout`. O bloco `/redesocial/` **não tem nenhuma**. Depois de uma purga ampla,
com a borda fria e os bots de treinamento sem teto por IP, N requisições concorrentes
chegam a um processo com `MemoryMax=768M`, cada uma executando a consulta de feed.
É o 9.2 acontecendo por outra porta. `FX-borda-social-sem-manada` estende o gate
`social-cache` que já existe, em vez de criar um novo.

**9.6 — IP real de visitante versionado no git, sem horizonte de apagamento.**
`git ls-files data/ops/access/ | wc -l` → **31 arquivos rastreados**, e a linha traz
`remote_addr` com o IP completo (o `real_ip_header CF-Connecting-IP` faz o IP real
chegar). História de git é guarda **para sempre**, espelhada no backup, e apagar exige
reescrever história — que o contrato proíbe. Hoje o par (IP, caminho) diz pouco, porque
só existe `/redesocial/`. No dia em que existirem `/perfil/{handle}/`, `/duvida/{slug}/`
e `/mensagens/`, o mesmo par liga pessoa identificável ao conteúdo jurídico que ela
leu — sensível pelo art. 5º, II da LGPD quando o tema for saúde. `FX-ledger-social-sem-ip-em-git`:
a linha social entra com IP pseudonimizado por HMAC datado, o IP bruto continua
existindo **fora do git**, com o prazo do art. 15 e o varredor apagando. É o inverso de
suprimir o dado: é guardá-lo onde a lei manda.

**9.7 — Três varredores prontos que ninguém aciona, e uma página pública que publica
o defeito.** `contas.LimparVencidos`, `lgpd.Varrer` (que faz `DELETE` de verdade) e
`moderacao.RevisarPrazos` têm **zero chamadores** fora de teste. Consequência medida:
`moderacaotransparencia` calcula `DivergenciaRevisarPrazos` comparando atrasadas no
banco com vencidas medidas — e como ninguém chama `RevisarPrazos`, esse campo nasce
**permanentemente verdadeiro**. A página pública de transparência publica uma
divergência que é defeito nosso. Fecha com um timer diário de manutenção, antes das
02:20 em que a série já roda.

**9.8 — Sanitização de UGC não é nomeada em lugar nenhum do plano.** E a peça já está
comprada: `bluemonday v1.0.27` no `go.mod`, **com ADR redigida** e registrada na
política de dependências, mais `htmlpolicy.newPublicBodyPolicy()` como política irmã
curada por allowlist. `script-src 'none'` mata `<script>`, mas não mata
`<a href="javascript:">`, `<img onerror>` nem markup desbalanceado — e markup
desbalanceado num corpo de dúvida quebra a tela e estoura o teto de 50 KB de um jeito
difícil de reproduzir. `FX-sanitizacao-de-ugc`: **uma** política para os dois canais,
porque o que o navegador bloqueia o agente consome.

**9.9 — O erro mais caro do plano: eu contradisse o oráculo que define "pronto".**
A refutação adversarial pegou, e eu confirmei contando: **23 provas do manifesto
amarram símbolos** aos pacotes que este plano redefiniu por conta própria —
**7** a `internal/socialdb` (incluindo **DDL**: `perfis_advogado`,
`UNIQUE(oab_numero, seccional)`, `'resposta'`), **11** a `internal/socialrender`
(`rel="next"`, `/pagina/`, `CC-BY-NC-ND-4.0`, `SevImportant`,
`dataHoraUltimaAtualizacao`) e **5** a `internal/consultapublica`.

E o plano dizia: DDL vai para `socialconteudo`, `socialdb` é só DSN, o render vira
`socialpage`, e nasce um `consultacorpus` ao lado. **Cada uma dessas decisões faz um
agente construir o que o gate reprova.** Ou ele segue o plano e o `entrega-final`
acusa `pacote_ausente`, ou segue o gate e viola o plano — e nos dois casos é retrabalho
de dezenas de milhares de linhas no meio da sessão.

**A correção, e a regra que ela fixa:** o manifesto **vence**. `internal/socialdb`
carrega o DDL, `internal/socialrender` é o nome do renderizador,
`internal/consultapublica` é o nome da consulta. Não é que minha divisão fosse pior —
é que a §4 deste plano diz "corrige-se a prova quando ela mede a coisa errada", e aqui
a prova **não** mede errado: ela mede uma arquitetura diferente, decidida antes, e
trocar arquitetura aprovada por preferência posterior é exatamente o retrabalho que o
contrato chama de regressão. Onde minha divisão agrega — um pacote importável pelos
dois processos, para a paridade dos quatro canais ser **por construção** —, ela entra
como acréscimo dentro de `socialrender`, sem renomear nada.

E o requisito não escrito continua valendo: se `cmd/server` importar esse pacote, ele
**não pode** conter literal `var/social`, `social.db` ou `WIKI_SOCIAL_*`, ou
`socialisolation` reprova o fecho inteiro do acervo.

**E duas correções de orquestração:** as ondas 1 e 1' são declaradas paralelas e
**editam o mesmo pacote** (`internal/contas` — uma tira o DSN, a outra acrescenta a
tabela de códigos), violando a regra do próprio plano; e `internal/checks/checks.go`
mais `content/redesocial_entregas.json` são **ponto de serialização de toda a sessão**
(nove gates novos e 163 entradas, tocados por quase toda onda). Os dois arquivos são
**do chefe**: o agente relata o nome do gate e a linha do manifesto, e eu escrevo.

---

## 10. Verificação

A verificação tem **três camadas**, e cada uma responde a uma pergunta diferente.
Nenhuma substitui a outra.

### Camada A — nada regrediu no ativo

O acervo indexado é o que não pode ser posto em risco. Cada invariante vira teste que
prova **por construção**, não por sonda:

| Invariante | Como se prova | O dano se cair |
|---|---|---|
| CSP × folha servida batem byte a byte | `TestNginxSecurityHeadersDoNotDriftFromGoConstants` compara `.conf` × constante Go, e `check-csp-style-hashes` compara `public/` × binário. **Nenhum dos dois tem gatilho automático** | as 10.141 páginas ficam **sem estilo** |
| `cmd/server` não referencia estado social | `internal/socialisolation`, por varredura AST de **literais** — ver a ressalva abaixo | um panic na rede social derruba MCP, A2A e as gêmeas |
| Sitemap social fora do índice do acervo | asserção nas duas direções, com o cenário literal do §11.1 | **`cmd/server` não sobe** — e leva o canal de máquina junto |
| `published_manifest` coerente | `publishedmanifest.Validate` no boot | 404 e página órfã no índice do buscador |
| Rastreio não caiu | `check-efeito-nos-bots`, com `--desde` **explícito** — ver abaixo | queda de rastreio é defeito de engenharia (R6), nunca "depende do bot" |

**Quatro achados que mudam onde os gates rodam:**

1. **A proteção do CSS existe e é boa; o que falta é acioná-la na hora certa.** O
   pre-commit **já** detecta o diff perigoso (`^(internal/(render|seo|httpserver)/|ops/nginx/security-headers\.conf)`)
   — e chama `check-analytics-contract`, que itera `script-src`, `connect-src` e
   `img-src` e **nunca** `style-src`. O gatilho certo dispara a ação errada. Correção:
   o mesmo bloco passa a rodar o teste de drift (comparação de string, sem tocar
   `public/`, barato); `check-csp-style-hashes` (20 s medidos, exige `public/` fresco)
   entra no **deploy**, entre a republicação e a parada do serviço — é o único ponto
   em que o `public/` está novo e o serviço antigo ainda de pé, então falhar ali
   aborta sem derrubar nada.
2. **`cmd/generate-csp-nginx` é código morto de proteção.** Ele existe justamente para
   tornar a dessincronização impossível — e **não tem teste algum** nem é chamado por
   deploy, hook ou timer. Passa a rodar no pré-voo do deploy (prevenção, ~1 s) e ganha
   teste que compara sua saída com a string exigida pelo teste de drift, fechando o
   laço gerador↔detector.
3. **Metade do gate de isolamento é estruturalmente vazia.** `cmd/social` é
   `package main`, e `package main` **não é importável em Go**: a asserção "o fecho do
   `cmd/server` não importa `cmd/social`" nunca pode disparar, com ou sem defeito. A
   proteção real é inteiramente a varredura de **literais** (`var/social`,
   `WIKI_SOCIAL_*`). Consequência prática: o vetor a temer não é import distraído, é
   **referência de string** — e um acoplamento que receba o caminho por parâmetro,
   sem literal no arquivo, escapa. Registro isso como limite conhecido, sem fingir
   cobertura que não existe.
4. **Uma onda social não move a referência de medição.**
   `check-efeito-nos-bots` deriva a data-base de `CAMINHOS_DE_REFERENCIA =
   ("internal/sitemap", "tools/deploy-publico")` — um deploy que só toca `cmd/social/`
   deixa a referência apontando para o último commit do acervo, e o veredito sai sobre
   a mudança errada. Toda medição de onda social usa `--desde <data-do-deploy>`
   explícito. É mais seguro que estender a lista, porque não mistura o efeito das duas
   frentes num veredito só.

### Camada B — a rede social realmente funciona

Quatro jornadas sobre servidor de teste + SQLite temporário: (a) cadastro →
confirmação → login → sessão → publicar dúvida → responder como verificado → feed;
(b) denúncia → fila certa → decisão → trilha íntegra, **table-driven sobre as sete
categorias**, não uma só; (c) art. 18 ponta a ponta; (d) tentativa de burlar cada
trava.

**Três armadilhas de harness que matariam a suíte inteira, achadas antes de escrever
a primeira linha:**

1. **`CookieDeSessao` marca `Secure: true`** (`sessao.go:328`) e um servidor de teste
   HTTP puro faz o cookiejar **recusar** devolver o cookie (RFC 6265 §5.4) — toda
   jornada pós-login morreria em `ErrSessaoInvalida`, e o sintoma pareceria bug de
   sessão. Harness usa TLS de teste.
2. **`http.Client` não envia `Sec-Fetch-Site`**, então `ConfereOrigem` (`csrf.go:77`)
   cai para `Origin` — que também não vem por padrão. Todo POST do harness seta os
   dois explicitamente.
3. **`superficie.TextoPublicado` só reconhece a página de regras** (`superficie.go:70-79`).
   `moderacao.Receber` a usa como âncora anti-invenção: sem estendê-la ao UGC,
   denunciar qualquer post devolve `ErrConteudoInexistente` e a jornada (b) não sai
   do lugar.

**O padrão mais forte, e este repo já o tem: teste de mutação.**
`internal/moderacao/gate_constraint_test.go:12` reescreve o schema **removendo** a
trava da tese 2 e prova que, sem ela, o `INSERT` proibido passa — com controle
positivo ao lado. Cinco travas existentes nunca foram vistas reprovando e ganham o
gêmeo mutante: os triggers append-only da trilha, o `CHECK` de revisor diferente do
original, `trecho_confere`, fila órfã e o `ON DELETE CASCADE` das sessões.

**As cinco provas que, se passarem, dizem que a rede social funciona** — cada uma com
a mutação que a derruba:

| Prova | Mutação que a faz cair |
|---|---|
| Resposta de advogado **não** verificado não tira a dúvida da banda `aguardando` | trocar a query do selo para ler `contas.papel` em vez do JOIN com `vigente_ate` |
| Decisão de honra sem ordem judicial é recusada **na rota HTTP**, não só no `INSERT` | um handler que "otimiza" chamando SQL direto em vez de `moderacao.Decidir` |
| Quarentena estourada sobrevive ao reinício do processo | trocar `orcamento_diario` por um `sync.Map` em memória |
| Eliminar conta zera o identificador nos **três** bancos | comentar um único `PseudonimizacaoDeRegistro` — o dump acha o `contaID` bruto |
| Backoff atrasa mas **nunca bloqueia**, e o ataque distribuído exige OTP | qualquer `estado='bloqueada'` escrito por tentativa de senha |

**Fixtures que jamais casam com pessoa real:** e-mail em `@wj-teste.invalid` —
`.invalid` é reservado por RFC 2606/6761 e nunca é registrável, ao contrário do
`.adv.br` que o repo usa hoje e que **é** um domínio comprável. CPF de fixture usa
dígito repetido (`111.111.111-11`), que a Receita nunca emite — com um teste-espelho
rodando cada um contra o mod 11 e exigindo que **todos reprovem**. Nada de número
checksum-válido em lugar nenhum: um número que passa no algoritmo é, em princípio, um
número que pode ter sido emitido.

**E uma prova do manifesto que reprova para sempre como está:**
`F1-registros-acesso-cifrados` aponta `pacotes_go: internal/registrosacesso`, mas o
código vive em `internal/lgpd/registrosacesso.go` — um **arquivo**, não um diretório.
O guardião faz `os.Stat` do diretório e acusa `redesocial_prova_pacote_ausente` para
sempre. Decido pela correção da prova, não do código: `RegistraAcesso` e `Varrer` são
coesos com o resto do LGPD e compartilham o mesmo banco; separá-los seria mover código
que funciona para satisfazer um rótulo.

### Camada C — os bots de alto valor aceitaram

Sem **jamais** forjar UA de bot, que é fraude e é barrado por hook. Três asserções, no
método de `check-efeito-nos-bots`: **(a)** sobre a config — zero `limit_req` no bloco
`/redesocial/` e o mapa `$wj_bot_allow` íntegro; **(b)** sonda com UA próprio
(`wikijuridica-superficie-probe/1.0` + `X-Warming-Request: true`) provando 200, HTML
textual completo sem JS e dentro do teto; **(c)** o comportamento real vem do **log de
origem**, depois do deploy.

**Primeiro, um comentário que mente — e a decisão do dono que o resolve.**
`nginx.conf:1662-1664` afirma que a herança dá "pista livre ao Googlebot, ao **GPTBot**
e ao **ClaudeBot**". Conferi o mapa `$wj_bot_allow` (`:396-449`): **GPTBot e ClaudeBot
não estão lá**. Quem tem chave vazia são os bots de busca e de usuário — googlebot e
variantes, bingbot, applebot, duckduckbot/duckassistbot, yandexbot, petalbot,
oai-searchbot, chatgpt-user, claude-user, claude-searchbot, perplexitybot/
perplexity-user, meta-*. Os de **treinamento** ficaram em tiers finitos (600 e 300
req/min).

**Ordem do dono, 2026-09-05: acesso TOTAL dos bots à rede social — inclusive os de
treinamento, com rate limits generosos para os famosos.** GPTBot e ClaudeBot entram no
mapa; nenhum bot legítimo fica de fora da superfície social.

O raciocínio de produto que sustenta a ordem, e que eu compartilho: o acervo existe
para ser **citado**, e quem cita é o modelo — que aprende com o que rastreia. Manter
bot de treinamento em tier apertado é otimizar banda contra o único canal de
distribuição que não se compra. A rede social, sendo a única do país legível por
agente (gêmea Markdown, MCP, A2A, lote), é exatamente o conteúdo que vale ser
aprendido.
A entrega, então, não é corrigir o comentário para descrever a exclusão: é **fazer o
código dizer a verdade que o comentário já dizia**. Concretamente: acrescentar os dois
a `crawl.RequiredValuableBots()` (`crawl.go:309`) e ao mapa do nginx, na mesma
passada — o teste `nginx_bot_policy_drift_test.go:90-94` exige que todo bot da lista
esteja no mapa, então mudar só um lado reprova, e é essa trava que garante que a
decisão não fique pela metade. Efeito medido a acompanhar: os dois saem dos tiers de
600/300 req/min e passam a rastrear sem teto, o que aumenta o consumo de banda e I/O da
origem — `crawler_error_budget.jsonl` e `origin_bot_traffic_daily.jsonl` são onde isso
aparece, e é o que se observa na semana seguinte.

Para `/redesocial/`, o que o gate precisa garantir continua sendo o mesmo: que
**nenhuma** das cinco `limit_req` do `server{}` seja substituída por uma declaração
local — a herança do nginx é tudo-ou-nada.

### O achado que reordena esta frente inteira: os bots já foram embora

Antes de qualquer número de rate limit, isto — `data/ops/bot_return_state.json`,
medido agora:

| Bot | Pico | Última visita | Queda |
|---|---|---|---|
| **ClaudeBot** | **43.065 req/dia** (07-08) | **2026-08-28 — 8 dias** | **−100%** |
| GPTBot | 16.456 req/dia | 2026-09-05 | **−100%** |
| Googlebot | 4.297 req/dia | 2026-09-05 | **−99,2%** |

E há **alerta de severidade alta, aberto e silenciado por cooldown**, dizendo
literalmente "claudebot (abandonou, 8d)". O bot que fazia 43 mil requisições por dia
parou, o alarme disparou, e ninguém investigou.

**Isso inverte a leitura que eu fazia.** Eu lia o zero de ClaudeBot como evidência de
que "a superfície estática é barata para eles" e de que o gargalo seria a dinâmica.
Não é: é a R6 do contrato — **queda de rastreio é defeito de engenharia até prova
medida em contrário**, e "depende do bot" é desculpa proibida. Abrir o mapa para um bot
que abandonou não traz um único fetch de volta enquanto a causa não for achada.

**A ordem do dono continua valendo e é executada** — acesso total, os dois no mapa,
tier generoso. O que muda é a **ordem**: primeiro `FB-causa-do-abandono` (por que três
bots caíram entre 99% e 100%: mudou robots? CSP? cadeia de certificado? o 503 abaixo?),
depois a abertura. Executar a abertura sem isso seria entregar um número maior para
um consumidor que não está lá — e ainda declarar sucesso.

**E o canal caiu na cara do GPTBot:** das 15 gêmeas Markdown que ele pediu, **8 foram
503** (1.987 bytes de página de erro). Ele recebeu 7 documentos de 15. Isso é candidato
direto à causa acima, e é medição que eu tinha na mão e não olhei.

### Quatro medições que eu tinha registrado errado, corrigidas

**Os 8.476 "301 desperdiçados" do `meta-externalads` são legítimos.** Refiz: são 301
de **barra final**, que `nginx.conf:1850-1856` torna obrigatório — servir 200 no
caminho sem barra é a duplicidade que a config existe para impedir, e metade deles foi
seguida pela forma com barra na mesma janela. Não há "correção" lícita. O agente
**já está catalogado** (BUG-095, e uma tarefa aberta em `PLANO_SUPERFICIE_BOTS`), e o
defeito real é outro e mais interessante: `crawler_error_budget` **ficou cego** porque
`agent_key` é `null` para UA fora do registry, então o detector de desperdício de 301
não o viu. A correção-raiz é **registrar o agente**, não criar série nova. E foi uma
rajada de um dia, não um regime.

**A base de bytes estava errada por 3×.** Eu usei 22.631 B, que é a média do HTML **em
disco**; o ledger grava `$body_bytes_sent`, **pós-brotli**: média real **7.172 B**.
Refeita a conta, a origem satura em ~141 mil r/m no melhor sample de uplink e ~73 mil
no pior — e o uplink citado (134,86 Mbit/s) é o **melhor de três** de um único ensaio
de 17 dias atrás, com pior amostra de 70,09. Números de capacidade nesta frente saem
do pior sample, não do melhor.

**E uma contradição interna minha:** eu escrevi que "elevar o teto da superfície
dinâmica fica para depois de medir". Mas **entrar no mapa `$wj_bot_allow` dá chave
vazia, que é global** — remove o teto da estática **e** da dinâmica no mesmo instante,
inclusive em `/buscar/` (que monta índice por requisição), no `/api/v1/lote` de 604 KB
e no `cmd/social` com 768 MB e sem `proxy_cache_lock`. Não dá para abrir só metade pelo
mapa. Ou o teto agregado por operador vem **junto**, ou a abertura espera por ele.

**E excedi a ordem sem perceber:** eu havia estendido o afrouxamento a cinco bots que
estão em `strict` (Bytespider, CCBot, ImagesiftBot, Applebot-Extended,
webzio-extended). A ordem do dono nomeia **GPTBot e ClaudeBot**. Os cinco ficam onde
estão até haver ordem ou medição que os justifique.

**Quatro medições que sustentam o desenho do acesso total:**

| Medição | Consequência |
|---|---|
| **`meta-externalads/1.1` é o maior crawler da origem: 12.986 requisições em dois dias, e 8.476 delas são 301** — 65,3% do orçamento do maior crawler do site desperdiçado em redirecionamento, sobre 8.558 caminhos distintos, todos no host canônico (não é o `www`→ápice). E ele **não está em lugar nenhum do repositório** | Corrigir os 301 devolve mais rastreio do que qualquer afrouxamento de tier. É a entrega de melhor retorno da frente inteira |
| **GPTBot não varre o acervo: usa o canal de máquina.** Das 20 requisições medidas, 15 são gêmea `.md` e uma é `/api/v1/lote` com **604.137 bytes**. **ClaudeBot: zero requisições em quatro dias** | A superfície cara para os de treinamento é a **dinâmica**, não os 10.370 arquivos estáticos. E é justamente a que não tem medição de capacidade nenhuma no disco |
| **A pista sem limite já é forjada:** 9 requisições com `bot_allow=1` e IP **fora** da faixa oficial da OpenAI, de 8 IPs distintos, declarando `ChatGPT-User` | Chave vazia por User-Agent é chave vazia para quem digitar o User-Agent. A verificação por faixa de IP deixa de ser refinamento e vira pré-requisito de abrir mais |
| **Não existe teto agregado por operador.** A chave é `$binary_remote_addr`, então `amazonbot` (332 IPs) tem hoje ~199 mil r/m autorizados e `meta-externalads` (406 IPs) ~1,2 milhão — contra um uplink que satura em ~44,7 mil r/m | O mesmo artefato que verifica identidade fornece a chave agregada. É a correção mais barata e mais valiosa: hoje "600 r/m por IP" não limita nada |

**E o que descobri sobre o estado da porta:** `ai-train=yes` **já está** no `robots.txt`,
e a Cloudflare está com `ai_bots_protection`, `ai_training`, `ai_search`, `ai_user` e
`crawler_protection` **todos desabilitados**, versionado. O acesso já era permitido; o
que mantinha os de treinamento em segundo plano era o **teto por IP**, não bloqueio.
Executar a ordem do dono é, então, uma mudança **puramente aditiva** — nenhuma seta
aponta para baixo: os verificados por faixa ganham um teto agregado generoso, os cinco
bots hoje em `strict` sobem para o tier padrão, e **nada do que existe hoje aperta**.
Elevar o teto da superfície **dinâmica** fica para depois de medir capacidade: `600
r/m × 604 KB` daria 35,8% do uplink de uma rota só, e inventar número aqui seria R3.

**A série de medição, e de onde ela sai.** `crawl_coverage_daily`,
`edge_bot_agents_daily` e `edge_bot_status_daily` vêm do GraphQL da Cloudflare e
carregam `sampled_dataset: true` — **amostrados, não servem** para o método do §11.8,
que exige log de origem. O substrato certo já existe:
`data/ops/access/nginx-*.jsonl` (`origin_access_nginx_v1`) já traz, por requisição,
`agent_key`, `bot_allow`, `bot_simulation`, `warming`, `route_class` e `status`. O
campo `superficie` nasce **em um lugar só** — `tools/generate-origin-access-ledger`,
junto de `route_class` —, o schema sobe para `v2` de forma aditiva, e daí sai
`social_bot_coverage_daily.jsonl` agregado por `(data, agent_key, superficie)`. Dois
cuidados que a investigação impôs: `verification_method` é **por agente**, nunca em
bloco (há faixa oficial de IP para Google, Bing, DuckDuckGo, Perplexity, Anthropic e
OpenAI; só rDNS para Yandex; **nenhum** método para SemrushBot — declarar "faixa
oficial" para todos seria a métrica mentindo a nosso favor); e a série registra
`requests_forged` — `bot_allow=1` com IP fora da faixa —, porque esse scanner já foi
medido entrando.

**E a honestidade sobre o prazo:** em 7 dias o veredito de crescimento × canibalização
só pode sair **INCONCLUSIVO**. O método exige 14 dias antes e 14 depois com N≥100 em
cada janela, e forçar um "passou" antes disso é o mesmo verde-por-construção que já
custou 15 dias de rastreio caindo com o gate mudo. O que é honesto aos 7 dias:
`requests_authentic > 0` com `superficie=redesocial` e `function ∈ {search, user}`;
uma leitura de `robots.txt` seguida, do mesmo agente autenticado, por um GET a
`/redesocial/sitemap.xml` em 24 h — prova de que a **segunda** diretiva `Sitemap:` foi
seguida; e um tripwire de aviso se o rastreio do acervo cair mais de 20%.

**A paridade dos quatro canais tem um pré-requisito que muda a arquitetura.** `pagina`,
`renderizaHTML` e `renderizaMarkdown` moram em `cmd/social` — `package main`, que
nenhum outro binário importa. Para a paridade ser **por construção** (como no acervo,
onde os quatro canais chamam a mesma função), o objeto de página e o renderizador
Markdown precisam sair para `internal/socialrender`, importável pelos dois processos.
Sem isso, só resta comparar bytes entre dois processos vivos — mais fraco, mais caro,
e sem resposta quando um está fora do ar. E vale registrar: **nem o acervo tem hoje**
um teste comparando o Markdown do MCP byte a byte com a gêmea; existe para gêmea × lote
(`api_lote_test.go:89`), e o MCP é garantido só por "chama a mesma função". O teste de
3 vias nasce aqui, para os dois.

**Um achado que é pior do que o plano supunha:** o §13.8 registrava "a licença da gêmea
social é CC-BY-NC-ND, não CC-BY". Conferido: `render.go` **não emite front matter
nenhum** — a gêmea social sai sem `license` alguma. Não é licença errada, é licença
ausente, e é mais grave. `pagemarkdown/frontmatter.go:26` é o modelo; a regra passa a
ser: `CC-BY-4.0` **somente** quando o autor bate com a identidade de `site.json`,
`CC-BY-NC-ND-4.0` em todo o resto, nunca omisso — e o mesmo discriminador de autoria
decide o tipo do JSON-LD (`Article` para conteúdo do publisher, `QAPage` ou
`DiscussionForumPosting` para terceiro).

**A divergência de 1.200 bytes tem correção conhecida neste repo.**
`cmd/social/rotas_test.go:15` fixa `50 * 1024` = 51.200 enquanto
`htmlcontract.HTMLBudgetBytes` = 50.000. O mesmo bug já ocorreu em
`internal/render/area_hub.go:19-27` e a correção foi um **alias**
(`AreaHubMaxHTMLBytes = htmlcontract.HTMLBudgetBytes`), não um literal. Consequência
que a aritmética do plano de origem não viu: a "Thread com 12 respostas" (47.620 B)
tem folga de **2.380 B (4,8%)** contra o teto real, não os 3.580 B (7%) que a tabela
do §13.6 registra — ela foi calculada sobre 51.200. Com o JSON-LD de `QAPage` pesando
mais que os 1.800 B estimados, essa folga precisa ser **remedida** antes de fixar as
12 respostas por página.

---

**A armadilha desta frente:** rodei agora os seis gates sociais —
`social-cache`, `social-csp`, `social-rate-bypass`, `social-sem-cors`,
`social-isolation`, `social-policy` — e **os seis passam**. Isso não é prova de nada
(R2): o `social-csp` passa porque a CSP autoriza `/redesocial/assets/`, que **não é
servido por location nenhuma** — ele valida uma promessa vazia. O teste real é
mantê-los verdes **depois** que a folha existir e for servida de verdade. O mesmo
vale para `redesocial-completude`, que passa hoje com 75 pendências, por desenho.

1. **Por onda:** `./tools/go-modern test -count=1 ./internal/<pkg>/` (focado, nunca
   full-tree) + o gate nomeado da onda por `./tools/go-modern run ./cmd/check <nome>`.
2. **Compilação:** `./tools/go-modern build ./internal/... ./cmd/...`.
3. **Smoke:** `./tools/check-http-smoke` — acervo, canal de máquina e rede social no
   mesmo passo.
4. **Regressão do ativo:** `tools/check-efeito-nos-bots` antes e depois da onda 7.
5. **Terminal:** `./tools/check-redesocial-entrega-final` **verde** — zero pendentes
   e toda entrega com prova no disco. É o único gate que distingue pronto de
   pendente; `redesocial-completude` passa hoje com 75 pendências, por desenho.
6. **Refutação adversarial** (`Agent` com `model: fable`) antes da onda 3 (identidade
   real), da onda 7 (âncora, irreversível) e da 6' (dinheiro).

---

## 11. Passo 0 — o que acontece nos primeiros minutos após a aprovação

Em ordem, e nada de onda antes disto:

0. **Antes de tudo, preservar o que já está no disco e não commitado.** A worktree
   tem 94 arquivos modificados e 47 não rastreados, e entre eles há **trabalho real da
   frente do molde do STF**: `cmd/generate-stf-informativo-pages/vizinho_no_mesmo_dia_test.go`
   (novo) e `contagem_test.go` (+62 linhas), que travam uma correção medida em
   2026-09-04 — 38 de 60 registros do shard publicavam "0 dias antes" porque
   `textoVizinhoArea` caía no plural genérico com `dias == 0`. Mais
   `cmd/generate-stj-sumula-pages/main.go` (+45/-10) e `proximidade_test.go`. Isso é
   exatamente `P0-molde-stf-informativo`, e é a **primeira** coisa a commitar — com
   `git add` de caminho exato, nunca por diretório, que já varreu trabalho alheio três
   vezes neste repositório. Nenhuma onda começa antes.
1. **Este dossiê vai para `docs/goal/PLANO_EXECUCAO_REDE_SOCIAL.md`.** `P0-plano`
   exige que plano viva no repositório; `~/.claude/plans/` não é caminho versionável e
   some. Commit leve, sem Go, sem lock.
2. **`sudo systemctl enable wikijuridica-social.socket wikijuridica-social.service`** —
   é o comando que faz a rede social sobreviver a um reboot. Hoje ela não sobrevive, e
   já há visitante real nela. Um comando, e é o de maior retorno do plano inteiro.
3. **Aditivo ao manifesto** (§1): **+61 IDs** nascendo `pendente` (o número saiu de
   confronto por script contra o manifesto, e os IDs existentes entram pelo rótulo
   literal — `F2-paginacao-por-caminho`, não `F2-paginacao` —, senão o aditivo cria
   entrega duplicada da que já está lá), um campo `onda` em
   cada entrega, o estado `suspenso` com `Motivo` obrigatório, e as **três provas
   erradas** corrigidas com o motivo escrito — `F4-intimacao-multitenant` (símbolo com
   quatro colunas), `F1-sqlite-import-allowlist` (`moderncSQLiteImportAllowed`, e a
   entrega vira `entregue`) e `F1-registros-acesso-cifrados` (o pacote é
   `internal/lgpd`). Mais `F05-dynamic-redirect-preserva-assets` reclassificada para
   `entregue`. Depois, `check-redesocial-completude` tem de continuar verde — se ficar
   vermelho, o aditivo está malformado e eu conserto antes de seguir.
4. **`tools/generate-social-tasklist`** e a primeira emissão de
   `docs/goal/TASKLIST_REDE_SOCIAL.md`, derivada do manifesto. É o painel que a
   execução consulta e que o dono lê para saber onde estamos.
5. **`data/ops/codex2_policy_baseline.json`** com as 234 falhas de hoje, datadas, para
   que regressão nova seja distinguível da dívida herdada.
6. **Allowlist de import** estendida aos 12 pacotes novos que vão guardar estado
   (`policy.go:4249`) — antes de a onda 2 escrever o primeiro `import`, senão cada
   pacote novo nasce reprovando.
7. **DECs**: Resend como exceção nominal datada; acesso total dos bots de treinamento;
   autoria de terceiro (§4); segunda PJ.

Só então a onda 1 começa. E cada um destes passos é **verificado no disco** antes do
seguinte — passo 0 executado sem conferência é como uma onda nasce sobre premissa
falsa.

---

## 12. Prompt de retomada — modo `/goal`

Para reabrir esta frente em qualquer sessão futura, cole o bloco abaixo. Ele carrega o
essencial sem depender de nada desta conversa.

```
/goal Rede social jurídica do /opt/wiki — levar a 100% de engenharia.

CONTRATO: leia /opt/wiki/CLAUDE.md e ~/.claude/CLAUDE.md antes do primeiro comando.
PLANO: docs/goal/PLANO_EXECUCAO_REDE_SOCIAL.md (execução) e
docs/goal/PLANO_REDE_SOCIAL.md (desenho jurídico e arquitetural, 2.407 linhas).
MANIFESTO: content/redesocial_entregas.json é o que o gate cobra — entrega que não
está lá não existe. Estado após o aditivo: 163 entregas — 29 entregues, 2 suspensas
com motivo, 132 a fazer, das quais 10 dependem de evento do mundo. São 122 por
engenharia, e é o que o goal cobra.
TASKLIST: docs/goal/TASKLIST_REDE_SOCIAL.md, DERIVADA do manifesto por
tools/generate-social-tasklist — regenere, nunca edite à mão.

CONDIÇÃO DE ENCERRAMENTO DO GOAL, e ela não é negociável: o goal só fecha quando
./tools/check-redesocial-entrega-final reprovar APENAS pelas dez entregas que
dependem de evento do mundo, cada uma com a linha dizendo qual evento falta. Zero
pendentes por engenharia, zero `suspenso` sem motivo, todo gate citado por entrega
`entregue` executado e verde. Relatório de progresso não encerra goal; onda fechada
não encerra goal; teste passando sem o gate não encerra goal.

COMO USAR O PLANO: siga-o com crítica, nunca cegamente. Ele já errou quatro vezes
dentro do próprio documento, e a §0 lista os erros. Medição de disco vence o plano;
contexto novo reabre decisão; corrija o plano na mesma sessão, com o motivo.

CADÊNCIA OBRIGATÓRIA: consulte o advisor antes de abrir cada frente, ao mudar de
abordagem, quando a medição contrariar o esperado e antes de declarar pronto — com o
entregável já durável no disco. Antes do que é caro de reverter (identidade real,
âncora do acervo, dinheiro), acione Agent model:fable pedindo REFUTAÇÃO com
evidência, nunca opinião.

ONDE ESTÁ O TRABALHO: 17 pacotes Go a criar, 9 gates, 21 rotas, o design premium dark
"Ônix & Ouro" e ~180 testes. As ondas estão na §3 do plano de execução, com as
dependências que não podem inverter.

PRIMEIRO ATO, se ainda não foi feito:
  sudo systemctl enable wikijuridica-social.socket wikijuridica-social.service
(hoje as units estão `linked`, não `enabled`: um reboot derruba a rede social e ela
não volta — e já há visitante real em /redesocial/.)

O QUE NÃO FECHA POR ENGENHARIA: dez entregas dependem de evento do mundo — usuário
real publicando, bot indexando, dinheiro entrando, ato societário, protocolo no CNJ,
host com porta 25 liberada. Estão nomeadas na §5. Entregue tudo até a fronteira e
diga o que falta; fabricar o terceiro é a fraude que o contrato proíbe.

REGRAS QUE MAIS CUSTAM SE ESQUECIDAS: Go só por ./tools/go-modern, nunca full-tree ·
cmd/check SEM argumento roda todos os gates e derruba o host · git add com caminho
exato, separado do commit, mensagem por -F · nunca reverter, nunca descartar
trabalho · gate que reprova código correto se corrige na PROVA, jamais relaxando o
gate · nenhum dado pessoal real em arquivo versionado · sonda interna com UA próprio
(wikijuridica-superficie-probe/1.0 + X-Warming-Request: true), jamais forjando bot.

Comece medindo o estado real no disco. Não confie em comentário, nem neste prompt.
```
