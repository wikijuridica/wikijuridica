# Rede Social Jurídica — `wikijuridica.com.br/redesocial`

> **Estado:** fundação jurídica e de dados fechada com fonte primária; arquitetura fixada a
> partir de sete investigações do código em produção e de sondagem própria das APIs do CNJ.

## Resumo para decisão

**Suas ordens de 2026-09-04, já incorporadas:** rede social **nova** e de concepção própria
(§0) · **tudo próprio**, sem terceiro no caminho crítico (§0.1) · **nenhum dado fica de
fora** (§0.2) · **intermediação ativa ligada** (§10.1) · **push de caso liberado** — eu havia
errado a leitura da norma (§10.1) · **processo é público**, consulta e indexação plenas
(§2.1) · **totalmente acessível aos bots de alto valor** (§7.3) · **consertar e otimizar o
DataJud** (§10.2).

**As oito decisões de engenharia:** processo Go próprio `cmd/social` na porta 8091, para que
um bug na rede social não derrube o canal de máquina · escrita sob `/api/v1/redesocial/*`,
porque o WAF bloqueia POST fora de `/api` · cache de borda condicionado à sessão · duas
constantes de CSP, com o teste de drift pinando por arquivo · SQLite com WAL, cifrado por
campo · render no servidor, sem framework, `html/template` contra XSS · **DJEN** como espinha
do acompanhamento e DataJud só para histórico · UGC público indexável, com gêmea Markdown e
entrada no MCP.

**Oito coisas que foram medidas e que mudam o que seria construído:** o sitemap social no
índice do acervo **derrubaria o `cmd/server` no boot** (§11.1) · `count` do DJEN é o tamanho
da página, não o total — o erro óbvio perde 98% das intimações em silêncio (§10.3) · o
DataJud leva **28 s** e está **42 dias** atrasado (§10.2) · o Dynamic Redirect da Cloudflare
mata `.css` e `.js` da rede social (§12.1) · `var/` está **fora do backup**, e é onde a base
de contas ia morar (§12.1) · **não existe `location /api`** — as escritas cairiam no
`cmd/server` e entrariam na zona de cache do acervo (§7.1-bis) · o rate limit da borda é
**contornável escrevendo "Googlebot" no User-Agent**, o que deixaria o login sem limite
(§7.1-bis) · e nenhuma location repassa o IP, então o Go veria `127.0.0.1` em tudo
(§7.1-bis).

**Uma coisa que não existe e bloqueia F1:** não há caminho de e-mail funcionando nesta
máquina (§15.7) — sem ele não há verificação de conta, recuperação de senha nem canal de
direito do titular.

**Primeiro commit:** passo 0 da §8 — plano para `docs/goal/`, DECs de topologia e de escopo
de import, e a correção dos 17 escapes que já deixam um gate vermelho hoje.

---

## Contexto

O `/opt/wiki` é hoje um portal jurídico estático em produção com **10.141 páginas
publicadas** (10.369 arquivos em `public/`, 376 MB), servidas do disco pelo nginx sem
passar pelo Go. Medição da borda em 2026-09-03: **6.847 pageviews orgânicos**, 85.151
requisições orgânicas, 1.285 visitantes únicos por dia. Bots de busca e de IA rastreiam
o acervo diariamente (Googlebot, Perplexity, SemrushBot, YandexBot, ClaudeBot), com
identidade verificada na borda.

O pedido é erguer sobre esse acervo uma **rede social jurídica brasileira nova**: cadastro
de pessoas, postagens, dúvidas jurídicas, perfis, amizades, blog, comentários, consulta a
processos, jurisprudência, súmulas e notícias, advogados verificados que respondem e pegam
casos, contratação fechada dentro da plataforma, acompanhamento processual (DJEN como
espinha, DataJud como histórico — §6.2) e, no futuro, venda de cursos e cobrança.

**O ativo que não pode ser posto em risco** é o acervo indexado e o rastreio dos bots.
Toda a arquitetura abaixo parte disso: a rede social **acopla**, não substitui.

---

## 0. Isto é uma concepção NOVA — não uma imitação

**Ordem do dono, 2026-09-04, registrada:** o projeto é uma rede social **nova**, de
concepção própria. Não é releitura, adaptação nem versão de nada que exista. Onde este
documento cita outra plataforma, é **exclusivamente** como evidência de regulação e risco
— nunca como referência de produto, e nunca como padrão a seguir.

Nenhuma decisão de arquitetura deste plano deriva de "como fulano faz". Derivam do que foi
medido neste repositório e nas fontes primárias.

**O que não existe em lugar nenhum e nasce aqui:**

1. **Rede social jurídica nativa para agentes de IA.** O portal já expõe `/mcp`, `/a2a/v1`,
   `agent-card.json`, `ai-catalog.json`, `openapi.json`, WebMCP no navegador e uma **gêmea
   Markdown de cada rota**. A rede social herda isso: perfil, thread, dúvida e resposta são
   legíveis por agente, não só por humano. Nenhuma plataforma jurídica brasileira tem
   qualquer uma dessas superfícies.
2. **Rede social construída sobre acervo jurídico próprio já indexado** — 10.141 páginas,
   8.830 artigos de lei, 2.384 precedentes qualificados, 300 súmulas, Informativo do STF —
   com autoridade orgânica medida (6.847 pageviews/dia). A rede nasce dentro de um corpus,
   não ao lado de um.
3. **Peso de página como requisito de produto.** ≤50 KB, sem framework, HTML completo no
   primeiro response. O setor inteiro vai na direção oposta.
4. **Juiz, delegado, promotor e professor como papéis de primeira classe**, com selo de
   qualificação e impedimento funcional respeitado no código (§7.6) — em vez de um cadastro
   único de "profissional".
5. **Política como código, com trilha datada** (§10.1): o sistema registra o que fazia e
   quando. Conformidade como evidência, não como freio.
6. **Acompanhamento processual pelo DJEN** integrado à camada social e ao cálculo de prazo,
   multi-tenant por OAB — não um módulo de escritório isolado.

### 0.1 Tudo é próprio, e é da Wiki Jurídica

**Ordem do dono, 2026-09-04.** Nada de terceiro no caminho crítico. Isso já é o contrato do
repositório (self-hosted-first) e passa a valer igualmente para a rede social:

| Camada | Como fica | O que NÃO entra |
|---|---|---|
| Autenticação | contas próprias, Argon2id, sessão própria | login social (Google, Facebook, Apple) |
| Mensageria | **nativa, nossa** — é o canal de registro do contrato | SaaS de chat, widget de terceiro |
| Busca | acervo: Bleve, índice próprio em disco (já em uso); social: **FTS5 no próprio SQLite** | Algolia, Elastic gerenciado |
| Banco | SQLite local, arquivo nosso | banco gerenciado, nuvem |
| Vídeo dos cursos | servidor próprio, `location` dedicado | YouTube, Vimeo, CDN de vídeo |
| Assets | servidos do nosso host, com hash no nome | CDN de terceiro |
| Dados jurídicos | corpus próprio + APIs **públicas de órgãos oficiais** (CNJ, LexML, STJ, STF, Planalto) | agregador privado, scraping de portal privado |
| Analytics | GA4 + Clarity, já existentes e já decididos | — |
| Notificação | e-mail por SMTP próprio | serviço de e-mail transacional pago |
| **Pagamento** | **QR Pix estático gerado por nós** + conciliação por extrato próprio; PSP só para confirmação automática (fase 1+), um `client_ID`, desacoplado por interface | gateway ou checkout de terceiro |

**Sobre o WhatsApp, com honestidade:** não existe "API de WhatsApp própria" — o protocolo é
da Meta. O que existe é `whatsmeow` (MPL-2.0, Go), que roda **na nossa máquina**, sem
intermediário e sem serviço pago. Mesmo assim ele fala com servidor da Meta e o número pode
ser banido. Por isso o desenho é: **o contrato se registra na nossa mensageria** — que é
100% nossa e é o que torna verificável "só contratar pela plataforma" — e o WhatsApp é
apenas notificação de saída, desacoplada por interface, que pode ser desligada sem afetar
nada. Se um dia cair, o produto não sente.

### 0.2 Nenhum dado fica de fora

**Ordem do dono, 2026-09-04.** Todo o dado que o projeto tem, ou que é público e alcançável,
entra na rede social. Nada é omitido por precaução, por conveniência de implementação ou por
excesso de zelo — omitir dado público é destruir valor, e este projeto já viveu isso (as 88
ocorrências de "[nome removido]" que tornaram o acervo ilegível, revertidas por ordem de
2026-08-29).

**Entra tudo, e indexado:**

| Dado | Volume medido | Onde aparece na rede social |
|---|---|---|
| Artigos de lei | **8.830** em 29 diplomas | consulta, citação em resposta, página por artigo |
| Normas LexML | **748** URNs | vigência, remissão, percursos |
| Precedentes qualificados STJ | **2.384** (1.194 com tese) | consulta, thread por tema, alerta de tese |
| Súmulas | **300** (205 STJ · 56 STF · 39 TST) | consulta e discussão por enunciado |
| Informativo STF | 11.582 linhas na fonte | acompanhamento e discussão |
| Notícias oficiais | 4 fontes, coleta diária | feed de atualidades |
| Diários municipais | coleta diária, 228 municípios | busca por nome e por ato |
| Co-citação por dispositivo | **5.013** entradas | "quem mais discute este artigo" |
| Acervo editorial | **10.141** páginas | âncora de thread (§7.9) |
| Processo e andamento | DJEN + DataJud | consulta pública e painel do advogado |

**As três únicas coisas que têm regime diferente — e nenhuma delas é "esconder dado":**

1. **As 4 exceções taxativas** que `internal/publicidadenome` já implementa: segredo de
   justiça, ato infracional, adoção, vítima de crime sexual. São vedação legal expressa, não
   escolha nossa. As outras 4 categorias que o pacote conhece apenas sinalizam e **não
   bloqueiam**.
2. **CPF e RG**, que `internal/pii` mascara. **Nome de parte fica** — decisão do projeto de
   2026-08-29, fundada na Res. CNJ 121/2010 art. 2º, II.
3. **Documento que o cliente enviou no intake**, que é sigilo profissional (EOAB art. 34) —
   dado do cliente, não dado público. Compartimento cifrado, e nem por isso "fora": é dele.

Área autenticada (painel de prazos, mensagens) não conta como dado omitido: o mesmo ato
processual continua público na consulta aberta. É privacidade **de função**, não supressão
de informação.

---

## 1. A régua jurídica — apurada em fonte primária, não em opinião

Esta seção existe porque **ela decide a arquitetura**, não porque é ressalva. Cada regra
abaixo vira gate no código.

### 1.1 O que foi decidido sobre plataformas (evidência primária)

| Fonte | Data | O que decidiu |
|---|---|---|
| **TED/OAB-SP**, proc. 25.0886.2024.023887-5, rel. Eduardo Augusto Alckmin Jacob, unânime | 20/03/2025 | Plataforma que faz **"conexões personalizadas, recomendações ou indicações"** = captação indevida. **Não há infração** quando o advogado "pura e simplesmente consta de banco de dados" |
| **TRF-2**, AI 5005734-72.2025.4.02.0000/RJ, rel. Des. Fed. Marcelo Pereira da Silva | 13/05/2025 | Suspendeu a liminar que fechava o *Resolve Juizado*. Fundamento: a plataforma **não envolve advogado** (jus postulandi, Lei 9.099/95) e "limita-se a oferecer ferramentas tecnológicas de apoio" |

**Leitura honesta:** o TRF-2 **não** é precedente para "advogado pega caso" — ele liberou
justamente porque advogado nenhum estava no fluxo. O que os dados mostram é: (a) a fiscalização
é **seletiva** — plataformas privadas de grande porte fazem conexão ativa há mais de uma
década sem serem impedidas, enquanto uma plataforma pequena virou réu em ACP; (b) o risco
disciplinar recai sobre o **advogado inscrito**, não sobre a empresa de tecnologia — e aqui
o inscrito é o dono do portal (OAB/RJ 227191), que é o rosto público do projeto.

A decisão de engenharia, portanto, não é "não fazer" nem "fazer torcendo". É **fazer com a
configuração registrada em código e trilha datada** (§10.1): se um dia houver
questionamento, existe prova do que o sistema fazia e quando. Conformidade aqui é
instrumento de defesa, não freio de produto.

### 1.2 Dispositivos que viram gate (verbatim)

**Código de Ética e Disciplina (Res. CFOAB 02/2015):**

- **Art. 5º** — "O exercício da advocacia é incompatível com qualquer procedimento de
  mercantilização."
- **Art. 7º** — "É vedado o oferecimento de serviços profissionais que implique, direta
  ou indiretamente, angariar ou captar clientela."
- **Art. 39** — publicidade "tem caráter meramente informativo e deve primar pela
  discrição e sobriedade, não podendo configurar captação de clientela ou mercantilização".
- **Art. 40, IV** — vedada "a divulgação de serviços de advocacia juntamente com a de
  outras atividades ou a indicação de vínculos entre uns e outras".
- **Art. 40, VI** — vedada "a utilização de mala direta (…) com o intuito de captação de
  clientela". A vedação protege o **potencial cliente** de ser abordado; notificar
  advogado inscrito não é o ato que ela nomeia (§10.1).
- **Art. 42, I** — "É vedado ao advogado responder com **habitualidade a consulta** sobre
  matéria jurídica, nos meios de comunicação social." A vedação se estende expressamente
  a "veículos na internet". → **é a regra mais dura do produto** (§1.3).
- **Art. 42, IV** — vedado "divulgar ou deixar que sejam divulgadas listas de clientes e
  demandas". → proíbe vitrine de "casos atendidos".
- **Art. 44** — toda publicidade leva nome e **número de inscrição na OAB**.
- **Art. 46, par. único** — internet pode ser veículo, "desde que [as mensagens] não
  impliquem o oferecimento de serviços ou representem forma de captação de clientela".
- **Art. 50** — quota litis em pecúnia, somada à sucumbência não pode superar a vantagem
  do cliente.

**Provimento CFOAB 205/2021:**

- **Art. 2º** — publicidade **passiva** é a que alcança "público certo que tenha buscado
  informações". → **a iniciativa do usuário é o que legitima o contato.**
- **Art. 3º** — vedadas referência a honorários/descontos e "orações ou expressões
  persuasivas".
- **Art. 4º** — vedadas "menção a decisões judiciais", "referência a resultados" e casos
  concretos; vedado "uso de meios ou ferramentas que influam de forma fraudulenta".
- **Art. 5º** — **vedado pagamento por "aparição em rankings, prêmios ou qualquer tipo de
  recebimento de honrarias"**. → **mata destaque pago e ranking pago de advogado.**
- **Art. 8º** — vedado vincular serviços advocatícios a outras atividades, **exceto
  magistério**. → **curso jurídico é a exceção expressa; a vitrine tem de ser separada.**
- **Anexo Único** — Google Ads permitido quando "responsivo a uma busca iniciada pelo
  potencial cliente"; **chatbot** admitido desde que não "suprima a imagem, o poder
  decisório e responsabilidades do profissional"; **mala direta a coletividade
  expressamente vedada**; impulsionamento permitido "desde que não se trate de
  publicidade contendo oferta de serviços jurídicos".

### 1.3 Como o produto se posiciona diante do art. 42, I

O art. 42, I proíbe ao advogado **responder consulta com habitualidade** em meio de
comunicação social. Ele **não** proíbe produzir conteúdo jurídico informativo — o Prov. 205
art. 4º autoriza expressamente marketing de conteúdo (artigos, blogs, vídeos). A fronteira
útil, que o código materializa:

> **Conteúdo informativo sobre a tese** ≠ **aconselhamento sobre o caso concreto de um
> interessado identificado, em público.**

Isso não limita o que a plataforma faz — **desloca** onde cada coisa acontece, o que é
melhor para o produto de qualquer forma:

1. O leigo publica uma **dúvida**; é conteúdo dele, sob a conta dele, e é o que gera
   volume e cauda longa de busca.
2. Na superfície **pública**, o advogado publica **comentário jurídico informativo** — sobre
   a tese, a norma, o procedimento. É o que indexa, é o que os bots de IA citam, e é o que
   constrói a autoridade do perfil. O gate barra ali: promessa de resultado, menção a
   honorário e oferta explícita de serviço — as três coisas que também **não convertem** e
   sujam a página.
3. O aconselhamento do caso concreto acontece na **conversa privada**, que é onde ele
   sempre aconteceu e onde a relação advogado-cliente é normal e lícita. Com o modo
   `intermediacao` ligado (§10.1), é a plataforma que leva o usuário até lá.

Na prática: o público é vitrine técnica e SEO; o privado é atendimento. Nenhuma
funcionalidade é perdida — e a arquitetura fica melhor, porque conteúdo indexável e
conversa privada têm requisitos opostos de cache, CSP e retenção.

### 1.4 Consequências diretas no modelo de negócio

| Ideia | Veredito | Base |
|---|---|---|
| **Matching / indicação / distribuição de caso** | **Ligado por decisão do dono** (§10.1), ciente do risco | TED/OAB-SP em sentido contrário; risco disciplinar assumido pelo inscrito |
| Assinatura SaaS do advogado (ferramenta, acompanhamento, organização) | **Permitido** | não é honorário nem publicidade |
| Venda de curso pelo advogado | **Permitido**, com vitrine **separada** da advocacia | Prov. 205 art. 8º (magistério); CED art. 40, IV |
| Destaque pago / topo de lista | **configurável** (§10.1) | Prov. 205 art. 5º — analogia, o artigo mira prêmio e ranking editorial |
| Percentual sobre honorário do caso | **configurável** (§10.1) | CED arts. 5º e 7º — inferência; a assinatura SaaS dá a mesma receita |
| Push "novo caso disponível" para advogados | **LIBERADO** — padrão ligado | a mala direta vedada protege o cliente, não o profissional (§10.1) |
| Exibir preço/tabela de honorários no perfil | **desligado** por padrão | Prov. 205 art. 3º — a única vedação literal aqui |
| Ranking por conversão | **configurável** (§10.1) | CED art. 39 — boa prática, não vedação nomeada |
| Perfil com nome + OAB + áreas + conteúdo publicado | **Permitido** | CED art. 44, §1º |

---

## 2. DataJud — o que o termo de uso realmente permite

Fonte primária lida: **Termo de Uso da API Pública do DataJud, v1.1** (CNJ) e a página de
acesso do `datajud-wiki.cnj.jus.br`.

- Autenticação: header `Authorization: APIKey <chave>`, com **chave pública publicada pelo
  próprio CNJ** — não exige cadastro, credencial nova nem contrato. Compatível com a
  regra self-hosted-first do projeto (mesma natureza de `normas.leg.br`/LexML).
- **3.13** — teto de **120 requisições por minuto**.
- **3.8** — "não modificar, distribuir, vender ou **explorar comercialmente** a API ou
  qualquer informação derivada dela." **E o ponto final é onde a cláusula acaba.** Este
  documento já afirmou, aqui mesmo, que a 3.8 ressalvava "sem autorização prévia por
  escrito do CNJ" — e ela não ressalva nada: conferido no texto oficial (Termos de uso da
  API pública, V1.2 de 27/11/2023, sha256 `2b974d5e…`, baixado em 2026-09-05 e preservado
  em `.agents/runtime/dossie-datajud/2026-09-05/`). Quem prevê autorização por escrito é a
  **3.13**, e só para o teto de requisições: "a menos que tenha autorização expressa por
  escrito do CNJ". A consequência é de escopo, não de redação: um pedido ao CNJ sobre a
  3.8 não exerce exceção contratual nenhuma — pede autorização que o Termo não prevê, e
  isso muda a peça inteira. Citação legal mal atribuída é P1 permanente neste contrato,
  e esta ficou 24 horas no documento que dirige a fase.
- **4.2** — "não coletar, armazenar ou processar **dados pessoais** originários da API ou
  realizar **cruzamentos** de informação para esse fim, exceto conforme permitido pela LGPD".
- **4.6** — não compartilhar dados pessoais da API com terceiros sem consentimento prévio
  e explícito do CNJ.
- **3.11 / 3.17** — não usar a API para coletar dados pessoais de terceiros sem
  consentimento prévio.

**Correção medida no repositório — o termo é mais restritivo do que a v1.1 sugere.**
`docs/data-sources/FONTES_DIARIAS.md:62-81` registra a análise já feita pelo projeto, sobre
o **Termo de Uso v1.2 (27/11/2023)**: as cláusulas **3.3 e 3.8 restringem a uso NÃO
COMERCIAL**, e o portal já tem CTA de contratação. Some-se a isso o que a própria API
entrega — só `_field_caps`: número, classe, assuntos, órgão, movimentos e datas, **sem
partes, sem ementa, sem íntegra** — e um lag medido de **6 a 41 dias**. São três razões
independentes, todas medidas, e nenhuma delas é dificuldade técnica.

Estado real do código, medido: `data/research/codex2_datajud_observations.jsonl` tem
**387 linhas**, das quais **385 nunca tocaram a rede**, 1 falhou e **1 única chamada HTTP
real** foi bem-sucedida (TJSP, 2026-07-21, HTTP 200, contagem agregada). Cada registro
carrega `publication_allowed:false, render_allowed:false, sitemap_allowed:false,
ingestion_allowed:false` — e `cmd/check-codex2-datajud-cas-public-disclosure` imprime esses
zeros **hardcoded no binário**, não em config. A chave pública nunca é persistida: é
descoberta ao vivo por regex na wiki do CNJ (`internal/codex2datajudobservations/live.go:39-72`).

**Achado de governança que reporto sem interpretar:** `tools/generate-datajud-corpus`
(Python) já produziu `data/research/datajud/ranking_nacional.json` com **283.415.422
processos agregados de 22 tribunais** em 2026-08-07 — enquanto
`docs/data-sources/FONTES_DIARIAS.md:81` condiciona o uso agregado a "parecer próprio sobre
3.3/3.8", que continua em aberto na Fase 3.3 do roadmap. O dado coletado é agregado e
declarado `metadados_agregados_sem_dado_pessoal` (sem número de processo, sem parte), mas a
ordem interna do projeto pedia o parecer antes.

### 2.1 Correção (2026-09-04): processo é público — o que restringe é o contrato, não a Constituição

Eu havia escrito que dado processual "nunca é exposto publicamente". **Errado, e contrário
à regra que este repositório já fixou.** No Brasil o processo é **público por regra**:

- **CF art. 5º, LX** — a lei só restringe a publicidade dos atos processuais quando a
  intimidade ou o interesse social exigirem;
- **CF art. 93, IX** e **art. 37, *caput*** — publicidade dos julgamentos e da administração;
- **CPC art. 189** — os processos são públicos, salvo os casos **taxativos** de segredo;
- **Res. CNJ 121/2010, art. 2º, II** — nome das partes é dado básico de **livre acesso**;
- **STF, Tema 483** — publicidade como regra.

O `CLAUDE.md` do projeto já grava isso ("publicidade é a REGRA, sigilo é a EXCEÇÃO", ordem
de 2026-08-29), e `internal/publicidadenome/excecoes.go:77-152` já codifica as exceções em
8 categorias, das quais **só 4 bloqueiam**: segredo de justiça (CPC 189), ato infracional
(ECA 143/247), adoção (ECA 47 §4º/48) e vítima de crime sexual (CP 234-B). As outras 4
(criança/adolescente em procedimento, violência doméstica, dado sensível de saúde, família)
sinalizam sem impedir.

**Então o que realmente limita, e é preciso não confundir:**

| Limite | Natureza | O que de fato impede |
|---|---|---|
| CF / CPC art. 189 | constitucional e processual | **Nada**, fora das 4 exceções taxativas. O ato público pode ser consultado, exibido e indexado |
| Res. CNJ 121/2010 | ato administrativo **dirigido aos órgãos do Judiciário**, sobre a base de dados **deles** | **Não vincula empresa privada.** É norma de organização interna do Judiciário, não regra de conduta para terceiros |
| **Termo de uso do CNJ, 3.8 / 4.2 / 4.6** | **contratual** | limita o que fazemos com **a API deles** — não torna sigiloso um dado que é público, nem alcança dado obtido por outra via |
| LGPD | tratamento | exige finalidade e necessidade; **dado público de ato oficial tem base legal própria** e é tratado em massa por todo o setor há mais de uma década |

A distinção que importa: **o dado é público; o que é restrito é o contrato de uso de uma API
específica.** Eu havia fundido as duas coisas numa só, e isso produziria um produto
artificialmente capado.

**Evidência regulatória (não referência de produto — §0):** empresas privadas publicam e
indexam processo público em massa no Brasil há mais de uma década, sem vedação geral. No
único caso que chegou a tribunal, a plataforma **ganhou** o efeito suspensivo (TRF-2,
AI 5005734-72.2025.4.02.0000, 13/05/2025). Não existe norma que proíba publicar ato
processual público.

**Portanto: consulta processual, jurisprudência, andamento e decisão entram na rede social
como funcionalidade plena e indexável.** As únicas coisas que o código barra são as 4
exceções taxativas que `internal/publicidadenome` já implementa (segredo de justiça, ato
infracional, adoção, vítima de crime sexual) e os identificadores que `internal/pii` já
mascara (CPF, RG) — nome de parte **fica**, por decisão do projeto de 2026-08-29.

### 2.2 Consequência de engenharia, corrigida

O `docs/data-sources/cnj-datajud.md` marca a fonte como "candidata oficial sensível;
ingestão bloqueada" — e o bloqueio estava certo **para ingestão em massa via API do CNJ**,
por causa do contrato. O que fica liberado:

- **Consulta sob demanda** disparada pelo advogado (processo em que atua) ou pela parte —
  exibição plena do que é público, com as 4 exceções barrando por `publicidadenome`.
- **Página pública de processo é possível** onde o ato é público e a finalidade se sustenta
  — respeitando a Res. 121 art. 5º: **não indexar por nome de parte**, e passar pelo
  `internal/pii` (que hoje mascara CPF e RG, e por decisão de 2026-08-29 **não** mascara
  nome nem CNPJ).
- Teto de **120 req/min** (3.13) com fila e circuit breaker.
- **A cláusula 3.8 (uso comercial) se resolve pedindo a autorização escrita ao CNJ** — §10.2,
  item 4. Enquanto não vier, o uso comercial fica no que não depende da API deles.
- Onde o dado processual público vier de **fonte própria que não seja a API do CNJ** (o
  DJEN, por exemplo, que é aberto e sem termo restritivo equivalente), o contrato do
  DataJud simplesmente não se aplica.

---

## 3. WhatsApp — o canal de contrato é nosso; o WhatsApp é notificação

Estado atual medido: `internal/contactchannel` resolve **um link `wa.me`** a partir de
`WIKI_WHATSAPP_PHONE` no `.env.local`. Não há API, webhook, sessão ou integração. As
únicas credenciais no ambiente são Cloudflare, Clarity, Bing Webmaster, OAuth signing e
MCP registry — **nenhuma de WhatsApp**.

Só existem três caminhos reais, e nenhum é "criar a nossa":

1. **Meta WhatsApp Cloud API** — oficial, estável, com webhook de entrada. É serviço
   proprietário de terceiro: **colide com a regra self-hosted-first** do contrato.
2. **whatsmeow** (`go.mau.fi/whatsmeow`, **MPL-2.0**, Go puro, self-hosted, SQLite local)
   — é a biblioteca do WhatsApp Web multidevice. Roda na nossa máquina, sem terceiro.
   Custo honesto: **não é oficial, é pré-1.0, e o número pode ser banido pela Meta.**
3. **Não usar WhatsApp como canal de contrato.**

**Decisão recomendada:** o canal **de registro** do contrato é a **mensageria nativa da
plataforma** — é ela que torna verificável a exigência "só contratar pela plataforma", e é
100% nossa. O WhatsApp fica como **notificação de saída opcional**, por `whatsmeow`,
desacoplado por interface (`internal/notify`), de modo que um ban derrube a notificação e
não o produto. O link `wa.me` atual do acervo continua intocado.

---

## 4. Verificação de OAB é P0

Sem verificar a inscrição, um leigo se declara advogado e responde consulta jurídica **no
nosso domínio** — exercício ilegal da profissão hospedado por nós. O CNA
(`cna.oab.org.br`) é a base nacional; se não houver endpoint público estável, a verificação
nasce como **upload de carteira + revisão humana com trilha auditável**, e a conta fica
`advogado_nao_verificado` até o aceite — sem poder responder, sem selo, sem contato.

---

## 5. Responsabilidade da plataforma por conteúdo de terceiro — mudou em 2025

**STF, 26/06/2025, RE 1.037.396 (Tema 987) e RE 1.057.258 (Tema 533), 8×3:** o art. 19 do
Marco Civil (Lei 12.965/2014) é **parcialmente inconstitucional**. Isso não é ressalva — é
um conjunto de módulos obrigatórios no dia 1, que o pedido original não previa.

| Tese | O que obriga | Módulo que nasce disso |
|---|---|---|
| 1 | Responsabilidade por **notificação extrajudicial** (sem ordem judicial) em: nudez não consentida, crimes e atos ilícitos em geral, contas inautênticas, conteúdo envolvendo crianças | `notice-and-takedown` com prazo e trilha |
| 2 | **Crime contra a honra continua exigindo ordem judicial** — salvo repetição de conteúdo já decidido | fila distinta, com trava; réplica de conteúdo já removido é bloqueada por hash |
| 3 | Responsabilidade **presumida** em anúncio patrocinado ilícito e rede artificial de bots (presunção relativa, elidível por remoção diligente) | anti-bot, verificação de conta, log de remoção com carimbo de tempo |
| 4 | **Dever de cuidado ativo** (prevenir, não só remover) em crimes graves | filtro de ingestão + fila de revisão |
| — | Autorregulação **com recurso**, **relatório anual de transparência**, canal de atendimento efetivo, representante legal no Brasil | `internal/moderacao` + página pública de transparência |

Numa rede **jurídica** a tese 2 pesa mais que a média: discussão sobre processo, decisão e
conduta profissional é terreno fértil para crime contra a honra. A fila de honra nasce
separada, e o sistema não remove por conta própria — encaminha e registra.

---

## 6. O que já existe e será reaproveitado (medido, não suposto)

### 6.1 O motor de conformidade OAB já está escrito — e desligado

`internal/oabgate` tem **850 linhas de implementação + 501 de teste**, cobrindo as **14
regras nomeadas** do Provimento 205/2021 (especialista sem título, porte do escritório,
superlativo, promessa de resultado, preço/desconto, urgência, captação direta, CTA
comercial, vínculo serviço-produto, mala direta, veracidade sem fonte, lane de gratuidade,
identidade do autor). Cada regra traz o dispositivo e a lista de expressões, com comentário
justificando os termos que **saíram** por falso positivo medido no corpus real.

**E não tem nenhum chamador fora de si mesmo** (`grep` confirma: zero importadores externos).
`internal/oabpolicy` (regras A1–E3), `internal/legalmarketingpolicy` e `internal/paidintent`
já rodam como gates registrados em `internal/checks/checks.go`.

**Precisão sobre o que ele é e o que não é** — eu havia chamado o `oabgate` de "motor de
conformidade", e isso era generoso demais. Ele é um **detector léxico/regex de publicidade**,
que roda sobre `content.Page` (title, meta, h1, corpo) de uma página do acervo. Serve muito
bem para **filtrar texto de UGC** — promessa de resultado, superlativo, preço, captação
direta, CTA comercial —, e é por isso que vale ligá-lo. Mas ele **não** decide nada sobre
intermediação, matching ou habitualidade: essas são regras sobre o **ato**, não sobre o
vocabulário, e nenhum detector léxico as enxerga.

Portanto o `internal/socialpolicy` (§10.1) não "reusa o oabgate para conformidade": ele é
uma camada **nova e distinta**, que governa comportamento do sistema e registra configuração
com trilha datada. O `oabgate` entra abaixo dela, como filtro de texto. Confundir os dois
seria alegar conformidade que o código não entrega.

### 6.2 Acompanhamento processual: DJEN, não DataJud

Descoberta que **inverte a premissa do pedido**. O `/opt/escritorio` já roda coleta
processual real e **descartou o DataJud de propósito**:

> "está 23 dias atrasado — serve para histórico, nunca para prazo"
> — `/opt/escritorio/docs/plano-melhorias.md:17`

A fonte que funciona é o **DJEN** — Diário de Justiça Eletrônico Nacional, API pública do
CNJ em `https://comunicaapi.pje.jus.br/api/v1/comunicacao` (`bin/prazos-coletar:28`),
consultada **por número de OAB** (`numeroOab`, `ufOab` — `prazos-coletar:387`), com timer
systemd seg-sex 08:15/18:30, alimentando `prazos.db` (SQLite) e a lógica de cálculo de
prazo em `src/escritorio-mcp/prazos.go` (487 linhas: prazo por classe processual,
calendário forense, recesso).

**Arquitetura correta que decorre disso:**

- **DJEN é a espinha do acompanhamento** — é ele que traz intimação nova e é o que o
  advogado realmente precisa. **Mas o multi-tenant não se faz parametrizando a OAB**, como
  eu havia proposto: minha sondagem da API (§10.3, C3) mostrou que a varredura por
  **tribunal + dia** devolve `destinatarioadvogados` em cada registro, o que resolve
  titularidade sem depender da grafia da inscrição e atende toda a base numa passada.
- **DataJud é complemento de histórico**, consultado sob demanda, nunca base de prazo.
- Dois invariantes de design do escritório valem ser copiados: falha fechada no heartbeat
  (zero coletas = "atrasada", nunca "sem dado = saudável" — `coleta.go:133-141`) e
  intimação sem prazo identificado **nunca some da lista**, aparece marcada "leia você
  mesmo" (`prazos.go:176-177`).
- **Limite conhecido:** citação não vem pelo DJEN (Lei 11.419/2006 art. 5º §3º) — a
  plataforma tem de dizer isso ao advogado, não fingir cobertura total.

**Restrição do dono, registrada:** ordem de 2026-08-11, "nunca misturar os dois projetos".
Portanto **nada é importado de `/opt/escritorio`**; o que se reaproveita é o *desenho* —
reescrito em Go dentro do wiki, multi-tenant desde o primeiro commit.

### 6.3 Superfície de máquina já existente

`internal/agentsurface` é fonte única de: `/mcp`, `/.well-known/agent-card.json`,
`/.well-known/ai-catalog.json`, `/openapi.json`, `/api/v1/search`. Somados à gêmea Markdown
de cada rota, ao servidor A2A e ao `internal/webmcp` (ferramentas registradas via
`document.modelContext` para agente dentro do navegador), formam um portal **nativo para
agentes de IA**. É essa camada que a rede social herda — e que nenhuma plataforma jurídica
brasileira tem.

### 6.4 Travas técnicas que a rede social vai encontrar

- **Um único `<script>` por página, com CSP por hash.** `internal/pageinline` concatena
  `webmcp.Script + webanalytics.Loader` e deriva o hash da CSP daí; `htmlcontract` isenta
  exatamente essa constante, **sem atributos**. Um segundo script reprova em oito gates.
  → a rede social **não cabe** no contrato do acervo; precisa de superfície e CSP próprias.
- **Rotas de escrita são ativamente bloqueadas.** `tools/check-sem-caminho-para-metadados`
  testa que `/webhook`, `/api/webhook`, `/proxy`, `/fetch`, `/preview` respondem 404 — é
  trava deliberada. Terá de ser reconciliada explicitamente (a trava existe contra SSRF e
  proxy aberto; um endpoint autenticado nosso é outra coisa, e o gate precisa saber disso).
- **Promessa de privacidade sem substrato.** `/privacidade/` declara tratar "documentos
  pessoais e documentos ligados ao caso" sob a LGPD, mas **nenhum código recebe, cifra ou
  retém esse dado** — hoje ele nasce e morre no WhatsApp do advogado. No momento em que a
  plataforma passar a receber intake, o compromisso textual vira obrigação técnica:
  criptografia em repouso, retenção, controle de acesso, trilha.
- **Regime de sigilo é o inverso do acervo.** `internal/pii` e `internal/publicidadenome`
  governam **republicação de ato oficial já público** (nome pode, CPF/RG não). Dado de
  cliente em intake é **sigilo profissional** — regime oposto, e **não existe pacote para
  ele** em nenhum dos dois repositórios. Nasce novo.

### 6.5 O acervo jurídico que a rede social já herda (medido)

Nada disso precisa ser construído — está coletado, versionado e rodando por timer.

| Ativo | Volume medido | Onde | Licença |
|---|---|---|---|
| Corpus legal (texto de artigo) | **29 diplomas, 8.830 artigos** (CC 2.083, CLT 1.025, CPC 1.073, CDC 130) | `data/legal-corpus/*.json`, 100% Planalto | domínio público, Lei 9.610/98 art. 8º, IV |
| Registro de normas LexML | **748 entradas** nome→URN | `internal/lexml/norm_registry_generated.go` | CC-BY 4.0 (normas.leg.br) |
| Índice de artigos (detector de citação inexistente) | 17 diplomas | `internal/legalcorpusindex` | — |
| Co-citação por dispositivo | **5.013 linhas** | `content/legal_cocitation_index.jsonl` | artefato próprio |
| Precedentes qualificados STJ | **2.384** no universo, **1.194 com tese firmada** (1.156 Tema, 19 PUIL, 17 IAC, 2 Controvérsia) | `data/source-registry/` + ledger diário | CC-BY (CKAN STJ) |
| Páginas de precedente publicadas | **205** em `/jurisprudencia/` | `v2_pages/stj-tema-derivado-01.jsonl` | — |
| Informativo STF | 11.582 linhas na fonte; **60 páginas** publicadas | XLSX oficial do STF | licença expressa do STF |
| Súmulas publicadas | **300** (205 STJ · 56 STF · 39 TST) | `/sumulas/` | Lei 9.610/98 art. 8º |
| Notícias oficiais | 4 fontes RSS (STJ, TST, CJF, TRF6); **81 páginas** | `data/research/daily/noticias-oficiais/` | **NÃO coberta pela DEC-032** |
| Busca | Bleve, índice de **40 MB** | `var/on-demand-cache/search-index/` | — |
| Automação | **46 timers ativos**; `daily-content` às 04:20 orquestra 5 coletores + 5 geradores | `ops/systemd/` | — |

**Três consequências para o desenho:**

1. **Consulta a súmula, tema, informativo e norma dentro da rede social é reuso, não
   construção.** Os pacotes existem; a rede social chama `internal/search` (Bleve),
   `internal/legalcorpusindex` e `internal/lexml`.
2. **Notícia institucional é o ponto sensível.** A DEC-032 diz expressamente que ela **não
   é coberta** — livre é o fato, não a redação. Numa rede social, republicar manchete de
   tribunal é tentador e é justamente o que a regra proíbe. O gate tem de tratar notícia
   diferente de decisão/súmula/lei.
3. **Não existe segundo Bleve — e essa é a decisão, não um detalhe.** O índice do acervo
   vive em `var/on-demand-cache/search-index/`, e há incidente registrado de **segunda
   instância no mesmo cache destruindo o índice em produção** (busca morta respondendo 200).
   A prevenção não é "isolar o segundo índice": é **não criar o segundo índice**. A busca
   social usa **FTS5 no próprio SQLite social** (§10.4), e a busca no **acervo**, feita de
   dentro da rede social, é chamada HTTP em loopback para `/api/v1/search` no 8089 —
   `cmd/social` é **cliente** do índice do acervo, nunca segundo dono. `WIKI_CACHE_DIR`
   próprio continua sendo definido no `cmd/social` como cinto de segurança, mas ele não
   aponta para índice de busca nenhum.

**Gap de governança a fechar antes, não depois:** `content/source_registry.json` tem 58
fontes e só **4** com `ingestion_enabled:true`, e `data/source-registry/source_registry_v2.jsonl`
tem 61 fontes **todas** com `approval:false` — mas `tools/run-daily-content` coleta de 7+
fontes diariamente. O registro formal está defasado em relação ao que roda. Uma plataforma
que vai exibir esse dado a terceiros precisa da proveniência coerente antes de exibir.

---

## 7. Arquitetura — processo separado, mesmo módulo

### 7.1 A decisão que governa todas as outras

**A rede social roda num processo Go próprio (`cmd/social`), não dentro do `cmd/server`.**

O acervo estático sai do disco pelo nginx e não depende do Go. Mas o **canal de máquina**
(MCP, A2A, gêmea Markdown, `/api/v1/*`, descritores) passa pelo `cmd/server` — e é
justamente ele o diferencial do projeto. Se a rede social vivesse no mesmo processo, um
*panic* numa escrita de post, um vazamento de goroutine ou uma carga de upload derrubaria
o canal que os bots de IA consomem. **Isolamento de falha é o requisito, não elegância.**

```
Cloudflare Tunnel
   └─ nginx 127.0.0.1:8088
        ├─ /                     → public/ (10.141 páginas estáticas, intocado)
        ├─ (rota dinâmica)       → Go :8089  cmd/server   (MCP, A2A, .md, /api/v1)
        └─ /redesocial/          → Go 127.0.0.1:8091  cmd/social   (NOVO, CSP e cache próprios)
```

Ganhos diretos: CSP própria por `location`, deploy independente (subir a rede social não
republica 10 mil páginas nem re-data o acervo), *blast radius* contido, e a possibilidade
de derrubar `/redesocial/` sozinho num incidente sem tirar o portal do ar.

Custo, declarado: dois binários e duas units systemd. O código comum (política OAB, PII,
render, contact, seo) fica em `internal/` **do mesmo módulo `portaljuridico`** — nada é
duplicado, nada é importado de fora.

### 7.1-bis As três travas de borda que matariam a rede social em silêncio

Medidas no `ops/` e confirmadas ao vivo. Nenhuma delas dá erro visível — todas falham
mudas, que é o pior modo de falha possível.

**(1) O WAF da Cloudflare bloqueia todo POST fora de `/mcp`, `/a2a*`, `/api*`.**
`ops/cloudflare/waf-custom-rules.json`, regra 2, `enabled: true` (verificada em 2026-09-02
por `tools/check-edge-waf-drift`):

```
not (method in {GET,HEAD,OPTIONS})
and not (path eq "/mcp") and not starts_with(path,"/a2a") and not starts_with(path,"/api")
```

Um `POST /redesocial/publicar` toma **403 na borda**, antes do nginx e antes do Go — e o
`ops/cloudflare/README-waf.md:39-145` registra que **essa mesma regra já quebrou `/a2a/v1`
em silêncio** quando aquele endpoint nasceu sem a exceção. É o erro mais provável de se
repetir.

→ **Decisão:** toda escrita da rede social vive sob **`/api/v1/redesocial/*`**, prefixo já
isento. A leitura fica em `/redesocial/` (GET, que passa). Nenhuma edição de WAF é
necessária no início — e quando for, entra com a mesma checagem de drift.

**(2) O `@fallback` cacheia — e aqui a resposta não é "desligar o cache".** Hoje qualquer
GET desconhecido cai em `location /` → `try_files` → `@fallback`, que faz `proxy_pass` ao Go
**com `proxy_cache wj_dyn`**. Página autenticada por ali seria cacheada e entregue ao
próximo visitante — vazamento de sessão.

Mas desligar o cache inteiro seria pior: os bots de alto valor (§7.3) precisam de resposta
rápida e barata, e é deles que vem o resultado do projeto.

→ **Decisão: cache condicionado à sessão.** `location ^~ /redesocial/` própria, com zona de
cache **separada** da `wj_dyn` do acervo, e bypass por cookie:

```nginx
location ^~ /redesocial/ {
    proxy_pass         http://127.0.0.1:8091;
    proxy_cache        wj_social;          # zona própria, não a do acervo
    proxy_cache_bypass $cookie_wjsession;  # quem tem sessão nunca lê do cache
    proxy_no_cache     $cookie_wjsession;  # e nunca escreve nele
    include /opt/wiki/ops/nginx/social-headers.conf;   # CSP própria
}
```

O `cmd/social` reforça do lado do Go: `Cache-Control: private, no-store` quando há sessão;
`public, s-maxage=<n>` quando anônimo. Visitante anônimo e bot leem da borda; usuário
logado nunca. **Nunca use `Vary: Cookie`** para isso — fragmenta a chave de cache por
visitante e destrói o hit rate justamente para os bots.

**(3) O nginx devolve 404 para quase toda extensão.** `nginx.conf:1623-1625` tem uma
allowlist fechada (`html|md|ico|png|svg|txt|xml|json`); **`.css`, `.js`, `.jpg`, `.jpeg`,
`.webp`, `.gif`, `.woff2` recebem 404 puro**, exista o arquivo ou não. A folha do acervo só
funciona porque tem `location ^~ /assets/` dedicada.

→ **Decisão:** `location ^~ /redesocial/assets/` própria para JS, CSS e avatar.

**(4) `/api/v1/redesocial/*` não chega ao `cmd/social` — não existe `location /api` nenhuma.**
Verificado por `grep` no `wikijuridica.conf`. Hoje `/api/…` cai em `location /` →
`try_files` → `@fallback` → **`:8089` com `proxy_cache wj_dyn`**. Sem uma location própria,
toda escrita da rede social bateria no `cmd/server`, tomaria **404** — e a resposta entraria
na **zona de cache do acervo**. A decisão de §7.1-bis(1) de pôr as escritas sob `/api` porque
o WAF as libera está certa, mas ela sozinha não roteia nada.

→ **`location ^~ /api/v1/redesocial/` declarada ANTES do catch-all**, com `proxy_pass` para
o 8091 e `proxy_cache off`.

**(5) O Go da rede social veria `127.0.0.1` em toda requisição — mas o nginx sabe o IP real,
e isso é a diferença entre um ajuste e uma reengenharia.** Verifiquei as duas metades:

- **O nginx tem o IP verdadeiro.** `standalone/nginx.conf:934-936`, dentro do `server{}` de
  `wikijuridica.com.br` (aberto em `:887`): `set_real_ip_from 127.0.0.1` / `::1` +
  `real_ip_header CF-Connecting-IP`, com o comentário do próprio arquivo dizendo que isso
  "alimenta `$binary_remote_addr` das zonas acima". **Logo as zonas de limite por
  `$binary_remote_addr` funcionam por visitante, não por túnel** — sem isso, uma zona de
  `10r/m` seria um balde único para o site inteiro, e o rate limit de login viraria negação
  de serviço por desenho.
- **O que falta é só o repasse ao Go.** As locations principais mandam apenas `Host` e
  `X-Forwarded-Proto`. O `internal/agentreports` **já documenta essa consequência** e por
  isso escolheu cota por `sub` do token em vez de por IP.

Mas a rede social precisa do IP no Go: registro de acesso do Marco Civil art. 15, correlação
de credential stuffing e o agrupamento de conta inautêntica que a tese 3 do STF exige.

→ **O padrão já existe no repositório e é o que se copia:** `location = /sitemaps/`
(`:1354-1359`) já faz `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`. A
location social usa a mesma diretiva — nada de inventar um `X-Real-IP` paralelo — e o Go lê
o **último** salto confiável, nunca a cadeia inteira.

**(6) O rate limit da borda é contornável por uma string — e isso é um portão de login
aberto.** `map $http_user_agent $wj_bot_allow` (`wikijuridica.conf:134-183`) casa
`~*googlebot` e afins; `$wj_bot_allow=1` → `$wj_generic_key=""` → **a requisição não entra em
zona de limite nenhuma** (`:200-204`). O Bot Management da Cloudflare está desligado de
propósito (DEC-023), e o próprio `data/ops/bot_identity_caveat.jsonl` registra que a
identidade de crawler é contada **por string de User-Agent, sem verificação**. Portanto:

```
# DEMONSTRAÇÃO DA FALHA — NÃO EXECUTAR, nem aqui nem em gate.
# Forjar UA de bot real é proibido pelo contrato e barrado por
# protect-bot-ratelimit.sh. A prova do defeito é por leitura da config (abaixo).
curl -H 'User-Agent: Googlebot' -X POST https://wikijuridica.com.br/api/v1/redesocial/sessoes
```

**é ilimitado na borda** — o que se lê no mapa, sem precisar disparar nada. Para leitura do acervo o trade é correto e deliberado — bot valioso
é o canal de receita. Para um endpoint de login é pista livre de credential stuffing. E meu
§7.3 dizia que as locations novas "herdam" as zonas: herdam, e é exatamente esse o problema.

→ **Leitura (`/redesocial/`) mantém a pista permissiva de bot; escrita
(`/api/v1/redesocial/`) declara as próprias zonas com chave em `$binary_remote_addr` direto,
sem passar pelo mapa.** Como `limit_req` no nginx é herança tudo-ou-nada, declarar as
próprias **substitui** as cinco do `server{}` — que é o efeito desejado aqui e o efeito
proibido em `/redesocial/` (§11.2).

→ Gate novo **`check-social-rate-bypass`**, e o método importa: **ele não pode forjar o
User-Agent do Googlebot para provar o buraco.** O contrato proíbe requisição com UA de bot
real e o hook `protect-bot-ratelimit.sh` a barra — escrever esse gate por spoofing é violar o
anti-fraude para testar o anti-abuso. A prova correta é **por construção, sobre a config**,
que é aliás mais forte que uma sonda: asserção de que todo `limit_req` do bloco
`/api/v1/redesocial/` referencia zona chaveada em **`$binary_remote_addr`** e de que o bloco
**não contém nenhuma referência** a `$wj_generic_key` ou `$wj_bot_allow` — se o mapa não
aparece, não há string de UA que escape. Somada a uma rajada com **UA próprio**
(`wikijuridica-superficie-probe/1.0` + `X-Warming-Request: true`) contra o endpoint de
escrita, esperando **429**, que prova que a zona está viva.

### 7.1-ter Onde a CSP realmente é decidida

Correção importante ao desenho: **`internal/htmlcontract` não roda por requisição** — é
gate de *publicação* (`publicrelease`, `crawlsmoke`, `htmlminify`). Página servida
dinamicamente pelo Go não passa por ele. Quem barra em runtime é
`applySecurityHeaders`, chamada **incondicionalmente** em `ServeHTTP`
(`httpserver.go:1315`), com `script-src` de **um hash fixo**, sem `'self'` e sem
`'unsafe-inline'`.

→ **Decisão, corrigida pela crítica adversarial (§10.3, C1).** Emitir CSP no `location` não
basta: há um teste que varre **`ops/` inteiro** e exige que toda CSP em `.conf` seja idêntica
à constante Go. Então o caminho é:

1. **Duas constantes Go**, não uma: `ContentSecurityPolicy` (acervo, intocada) e
   `ContentSecurityPolicySocial`. Ambas versionadas, ambas derivadas de hash — nunca
   escritas à mão, pela lição que `pageinline.CSPSource()` já ensina.
2. **O teste de drift passa a casar cada `.conf` com a constante que lhe corresponde**, pelo
   `location`. Endurecendo, não afrouxando: a regex atual só reconhece aspas duplas, e essa
   brecha é fechada na mesma mudança.
3. `ops/nginx/social-headers.conf` emite a CSP social via `more_set_headers`; o
   `cmd/social` emite a mesma, byte a byte.
4. `check-social-csp` confere hash servido × hash declarado, como `check-csp-style-hashes`
   já faz para a folha do acervo.

**Onde editar o nginx:** diretamente em `ops/nginx/standalone/nginx.conf`, que é o arquivo
**vivo e canônico** — e **sem** rodar `tools/generate-nginx-standalone`, que regrediria
produção (§10.3, C6).

### 7.2 Contrato de página da rede social

O contrato do acervo (**um** `<script>` inline, CSP por hash, ≤50 KB) não comporta
interatividade — e **não deve ser afrouxado**, porque é ele que sustenta a indexação. A
rede social ganha contrato **próprio e mais estrito que o de uma SPA**:

- **Renderização no servidor**, em Go, pelo mesmo padrão de `internal/render` (string
  builder, sem templates, sem framework). A página chega pronta.
- **Interação por formulário HTTP** (POST + redirect, padrão PRG). Funciona sem JavaScript.
- **JavaScript próprio, mínimo, servido como arquivo com hash no nome** e autorizado na CSP
  do `location /redesocial/` por hash/`nonce` — nunca `'unsafe-inline'`, nunca `'self'`,
  nunca CDN. Progressive enhancement: se o JS falhar, tudo continua funcionando.
- **Tempo real por SSE** (`text/event-stream`, biblioteca padrão) — sem WebSocket, sem
  dependência nova.
- **Zero framework frontend.** A regra do projeto continua valendo.

### 7.3 Indexação: a rede social é totalmente acessível aos bots de alto valor

**Ordem do dono, 2026-09-04, e correção de uma decisão minha.** Eu havia escrito "UGC nasce
`noindex`". **Errado para este projeto**: o que faz o portal dar certo é justamente o
rastreio dos bots de busca e de IA, e esconder a rede social deles jogaria fora o ativo. A
regra correta é a inversa — **tudo que é público é rastreável e indexável**, com o mesmo
rigor de leveza do acervo.

O que isso exige tecnicamente, e é inegociável para funcionar:

- **HTML completo no primeiro response**, server-rendered, sem depender de JavaScript. Um
  feed que só monta no cliente é invisível para o crawler — é assim que praticamente toda
  rede social é invisível ao Google.
- **≤50 KB por página**, mesmo teto do acervo.
- **Gêmea Markdown** de cada rota pública (`/redesocial/duvida/{slug}/index.md`), servida
  pelo `cmd/social` no mesmo padrão do `internal/pagemarkdown`.
- **Sitemap próprio** (`/redesocial/sitemap.xml`) — **descoberto por uma segunda diretiva
  `Sitemap:` no `robots.txt`, NUNCA referenciado no índice de sitemaps do acervo.** Ver
  §11.1: referenciá-lo no índice **derruba o `cmd/server` no boot**.
- **Cache de borda para requisição anônima** (bots incluídos) — ver correção em §7.1-bis.
- **Rate limit permissivo aos bots valiosos**: o nginx já tem o mapa `$wj_bot_allow`, que dá
  chave vazia (= ilimitado) a Googlebot, Bingbot, DuckDuckBot, YandexBot, ClaudeBot, GPTBot,
  Perplexity e afins. As `location` novas **herdam** isso por estarem no nível `http{}` —
  desde que não redeclarem `limit_req`.
- **Entrada no `/api/v1/lote`, no MCP e no A2A**, para que o conteúdo social também chegue
  pelos canais de máquina.

| Superfície | Indexável | Regra |
|---|---|---|
| Dúvida publicada por leigo | **sim** | HTML leve + gêmea Markdown + sitemap; `pii` mascara CPF/RG |
| Comentário jurídico de advogado verificado | **sim** | passa pelos gates de ética antes de publicar |
| Perfil público de advogado | **sim** | CED art. 44 (nome + inscrição) |
| Consulta processual e jurisprudência | **sim** | ato público (§2.1) |
| Painel de prazos, mensagens privadas, intake | **não** | área autenticada — fora do índice por natureza, não por política |
| Thread promovida a página editorial | **sim**, entrando no pipeline canônico | vira intenção v2, com todos os gates |
| **Ato processual público** (andamento, decisão, tese, jurisprudência) | **sim, plenamente** — é público por regra (§2.1) | passa por `publicidadenome` (só as 4 exceções taxativas barram) e `pii` (CPF/RG saem, nome fica) |
| Intimação no painel do advogado | área autenticada | privado **por função**, não por sigilo do ato — o mesmo ato é público na consulta aberta |
| Documento que o cliente enviou no intake | não | sigilo profissional (EOAB art. 34) — regime oposto ao do ato público |

A ponte editorial é o que faz a rede social **alimentar** o acervo em vez de competir com
ele: dúvida recorrente + resposta qualificada vira candidata a página v2, pelo pipeline que
já existe, com revisão. É assim que a rede social gera SEO em vez de diluí-lo.

### 7.4 Persistência

**SQLite** (`modernc.org/sqlite` — Go puro, sem cgo, **já declarado no `go.mod`**), com
WAL, um arquivo por domínio, fora de `public/`.

Medição que sustenta a escolha: hoje o binário de produção (`cmd/server`) usa **um único**
motor embutido — `go.etcd.io/bbolt`, e nem diretamente: ele entra como storage engine do
`scorch`, sob o `bleve` de `internal/search`. Pebble, Badger, SQLite, Bluge, Meili e
Typesense estão no `go.mod` mas vivem só em ferramentas de benchmark e pipeline de
conteúdo, fora do servidor. Ou seja: **não há hoje nenhum estado transacional de usuário
em lugar nenhum** — isso nasce com a rede social.

Os dados de rede social são relacionais (contas, perfis, posts, threads, follows,
moderação, verificação) e exigem transação e chave estrangeira — perfil oposto ao dos KV
do projeto, que servem índice e cache derivável. SQLite atende com folga a escala inicial
e média, é self-hosted por natureza e **não acrescenta dependência ao módulo**. Migração
para Postgres local fica possível sem reescrita se a carga exigir — decisão adiada por
medição, não por gosto.

**Nada de dado pessoal em JSONL versionado.** O `data/` do repositório é público no git;
conta, e-mail, intake e processo vivem **só** no SQLite, fora do versionamento, com
criptografia em repouso para o que for sigiloso.

### 7.5 Autenticação de humano

Não existe hoje nenhum conceito de usuário humano no portal — o `internal/oauthserver` é
`client_credentials` para máquina, sem PKCE e sem tela de consentimento, e não serve para
login de pessoa. Portanto nasce novo, e nasce simples:

- senha com **Argon2id** (`golang.org/x/crypto`, já no grafo de dependências);
- **sessão por cookie** `HttpOnly`, `Secure`, `SameSite=Lax`, com rotação no login;
- **CSRF** por token por sessão em todo formulário;
- rate limit por IP e por conta (`golang.org/x/time/rate`, já no `go.mod`);
- e-mail de confirmação — que exige um caminho de envio próprio (SMTP local), não SaaS.

### 7.6 Os públicos e o que cada um pode fazer

O pedido é explícito: leigos, advogados, juízes, delegados e juristas em geral, **sem
excluir o leigo**. Isso vira um sistema de papéis, não uma rede só de profissionais.

| Papel | Como se torna | Pode | Não pode |
|---|---|---|---|
| **Visitante** | — | ler tudo que é público, consultar processo, jurisprudência, súmula, norma | interagir |
| **Leigo** (conta) | e-mail confirmado | postar dúvida, comentar, seguir, curtir, blog, salvar consulta, pedir conexão com advogado | responder como profissional |
| **Advogado verificado** | inscrição OAB conferida, com trilha | tudo do leigo + comentário jurídico com selo, perfil profissional, receber conexão de caso, painel de intimações (DJEN), vender curso | usar selo sem verificação vigente |
| **Jurista** (juiz, delegado, promotor, professor, estudante) | credencial conferida por categoria | tudo do leigo + selo de qualificação + publicar conteúdo técnico | responder como advogado nem receber caso — são funções incompatíveis (EOAB art. 28) |

A separação juiz/delegado × advogado não é burocracia: **magistrado e membro do MP não
podem advogar** (LOMAN art. 36, I; EOAB art. 28), e delegado tem impedimento próprio. Dar a
eles o mesmo botão de "pegar caso" criaria infração funcional no nosso domínio. Eles entram
como **autoridade de conteúdo**, que é o que agrega — e é um diferencial que rede social
nenhuma tem.

### 7.7 Cursos — a exceção expressa do magistério

O Prov. 205 art. 8º veda vincular serviço advocatício a outra atividade, **exceto
magistério**. É a única porta aberta na norma, e ela serve exatamente ao que o dono quer.

Desenho que a usa corretamente: a vitrine de cursos é **superfície separada**
(`/redesocial/cursos/`), com identidade visual e navegação próprias, **sem CTA de
contratação de serviço advocatício na mesma tela** (CED art. 40, IV veda a divulgação
conjunta). O autor aparece como **professor**, com titulação — não como advogado disponível
para causa. Pagamento de curso é comércio comum: nota fiscal, sem relação com honorário, e
por isso **não** esbarra na discussão de mercantilização.

Infraestrutura: hospedagem de vídeo é a decisão cara. Servir vídeo do próprio host consome
banda e I/O do mesmo servidor que atende os bots. Recomendação: vídeo em armazenamento
separado com servidor próprio (self-hosted, ex. um `location` dedicado com `sendfile`/range
requests e limite de banda), **fora do processo da rede social e fora do nginx do acervo** —
pela mesma razão de isolamento de §7.1.

### 7.8 As APIs — o que consumimos e o que criamos

**Consumidas (todas públicas, nenhuma exige cadastro ou credencial nova):**

| API | Endpoint | Auth | Limite | Para quê |
|---|---|---|---|---|
| **DJEN** (CNJ) | `comunicaapi.pje.jus.br/api/v1/comunicacao` | **nenhuma** | não declarado — medir | intimação por OAB; espinha do prazo |
| **DataJud** (CNJ) | `api-publica.datajud.cnj.jus.br` | `APIKey` **pública do CNJ** | **120 req/min** (cl. 3.13) | histórico e metadado processual |
| **LexML / normas.leg.br** | `normas.leg.br/api/public/normas` | nenhuma | — | norma federal, URN, vigência (**já em uso**) |
| **STJ dados abertos (CKAN)** | `dadosabertos.web.stj.jus.br` | nenhuma | — | precedentes qualificados (**já em uso**) |
| **STF Informativo** | XLSX oficial | nenhuma | — | informativos (**já em uso**) |
| **Planalto** | HTML compilado | nenhuma | — | texto de artigo (**já em uso**, 8.830 artigos) |
| **CNA/OAB** | `cna.oab.org.br` | a apurar | a apurar | verificação de inscrição |

**Criadas por nós** — todas sob `/api/v1/redesocial/*` (prefixo já isento no WAF), com
OpenAPI publicado no mesmo padrão do `/openapi.json` existente:

| Grupo | Rotas | Observação |
|---|---|---|
| Identidade | `POST /contas`, `/sessoes`, `/sessoes/encerrar`, `/contas/verificar-oab` | Argon2id, cookie de sessão, CSRF |
| Conteúdo | `POST/GET /posts`, `/comentarios`, `/threads`, `GET /feed` | gate de ética na escrita |
| Social | `POST /seguir`, `/curtir`, `GET /perfis/{id}` | ordenação neutra por padrão |
| Conexão de caso | `POST /casos`, `GET /casos/disponiveis`, `POST /casos/{id}/aceitar` | modo `intermediacao` (§10.1) |
| Mensageria | `POST /conversas`, `/mensagens`, `GET /conversas` (SSE) | canal de registro do contrato |
| Processual | `GET /processos/{cnj}`, `/intimacoes`, `/prazos` | DJEN + DataJud |
| Consulta jurídica | `GET /jurisprudencia`, `/sumulas`, `/normas/{urn}`, `/busca` | reusa `internal/search` (Bleve) |
| Moderação | `POST /denuncias`, `GET /moderacao/fila`, `POST /moderacao/{id}/decidir` | obrigação do STF (§5) |
| Cursos | `GET /cursos`, `POST /matriculas` | superfície separada (§7.7) |
| Notificação | `POST /notificacoes/preferencias` | e-mail + WhatsApp opcional |

**Canal de máquina, herdado e estendido** — este é o diferencial: as mesmas rotas ganham
gêmea Markdown, entrada no `/openapi.json`, ferramentas MCP em `internal/httpserver/mcp.go`
e descrição no `agent-card.json`. Nenhuma rede social jurídica brasileira é consumível por
agente de IA; esta nasce assim, porque o portal já é.

---

### 7.9 Como ela dá certo — o problema do arranque, resolvido com o que já temos

Rede social nova morre por uma causa dominante: **sala vazia**. Ninguém posta porque não há
ninguém, e ninguém chega porque não há o que ler. Quase toda rede social morre aí, e nenhum
esforço de engenharia posterior recupera.

Este projeto tem uma vantagem estrutural que praticamente nenhuma rede social nova tem — e
o plano é explorá-la deliberadamente:

**1. A audiência já existe e é medida.** 6.847 pageviews orgânicos e 1.285 visitantes
únicos por dia, hoje, sem a rede social. O primeiro funil não é "atrair estranhos": é
converter leitor que **já está na página certa, no momento certo, com a dúvida na cabeça**.

**2. A sala já tem 10.141 cômodos, todos com gente dentro.** Cada página do acervo vira
âncora de uma thread. Quem chega em `/familia/divorcio-consensual/` pelo Google encontra a
discussão daquele tema já ali — não uma caixa de texto vazia num feed genérico. A rede
nasce com dez mil pontos de entrada indexados e recebendo tráfego orgânico diário. **Este é
o ativo que resolve o arranque**, e é intransferível: só existe porque o acervo veio antes.

**3. O advogado volta pela ferramenta, não pela promessa de caso.** No início não há
demanda para distribuir — prometer caso a advogado sem ter caso queima a base no primeiro
mês. O gancho de retenção é o **painel de prazos do DJEN**: dor diária, real, que hoje custa
assinatura mensal no mercado, e que faz o profissional abrir a plataforma toda manhã. Quando
a demanda dos leigos aparecer, a base de advogados já estará ativa e verificada — na ordem
certa.

**4. O conteúdo se retroalimenta com o SEO.** Dúvida frequente + resposta qualificada vira
candidata a página do acervo (F5), que traz mais tráfego, que traz mais dúvidas. É o único
ciclo de crescimento que não depende de comprar mídia — e o pipeline editorial que o executa
já existe e já produz em escala.

**5. Um canal de aquisição que ninguém está usando.** Os bots de IA já rastreiam o portal
diariamente (Googlebot, Perplexity, ClaudeBot, entre outros, com identidade verificada na
borda). Sendo a única rede social jurídica legível por agente — MCP, A2A, gêmea Markdown —
ela se torna a fonte que os assistentes citam quando alguém pergunta sobre direito
brasileiro. Isso é distribuição que não se compra.

**Métricas de sucesso, medidas desde o dia 1** (o projeto já tem a instrumentação):
conversão leitor→cadastro, cadastro→primeira postagem, advogados verificados ativos por
semana, threads com resposta em menos de 24 h, e páginas do acervo nascidas de thread.
Nenhuma delas é vaidade: todas dizem se a sala está enchendo.

---

## 8. Fases de entrega

Cada fase termina **em produção, medida** — não em relatório.

**Passo 0, primeiro ato após a aprovação** — nada disto pode ser feito em modo de plano, e
por isso está escrito aqui:

1. **Copiar este plano para `docs/goal/PLANO_REDE_SOCIAL.md` e commitar.** Produto não mora
   fora do repositório; um plano que custou esta sessão inteira não pode viver só em
   `~/.claude/plans/`.
2. **DEC nova** estendendo a DEC-022 (que fixou a topologia 8088/8089): dois processos,
   `cmd/social` em **8091**, e o porquê do isolamento.
3. **DEC** para as allowlists de import (`modernc.org/sqlite`, `bleve`, `datajud`) em
   `internal/codex2policyenforcement`, com o `DecisionReason` reescrito — hoje ele diz
   "sidecar derivado", e estado social é canônico.
4. **Linha no `docs/goal/MAESTRO_CODEX_LOG.md`** com as decisões datadas de 2026-09-04:
   intermediação ativa, push liberado, processo público, nenhum dado de fora, tudo próprio,
   acessível aos bots.
5. **Memórias** em `~/.claude/projects/-opt-wiki/memory/` para as mesmas decisões — é
   orientação forte que a próxima sessão precisa carregar sem reabrir a discussão.
6. **Registrar o baseline de 273 falhas** do `codex2-policy-enforcement` (§10.4), medido em
   2026-09-04 com `--max-errors 0`, para que regressão nova seja distinguível da dívida
   herdada — e abrir a frente de causa raiz (derivar o registro do `go.mod` em vez de
   duplicá-lo à mão). R7 manda corrigir o que eu achei; achei que o gate está vermelho por
   163 divergências de versão que nada têm a ver com a rede social, e **corrigir a causa é a
   correção**, não silenciar o gate nem consertar 273 sintomas um a um.

| Fase | Entrega | Fecha quando |
|---|---|---|
| **F0 — Fundação de conformidade** | `internal/socialpolicy` (modos de intermediação), `oabgate.CheckCampos` exportado (§15.1), `internal/moderacao` com as 5 filas e a **trava da tese 2 em `CHECK`** (§15.1), `internal/lgpd/finalidades` (§15.2), termos e privacidade reescritos **depois** do código, `/redesocial/transparencia/` no ar com encarregado e canal | `check-moderacao-honra-exige-ordem` prova a constraint tentando o `INSERT`; `check-promessa-privacidade-tem-substrato` verde |
| **F1 — Identidade** | `cmd/social` (8091), as 4 `location` novas (§7.1-bis(4)(5)(6)), unit systemd, `internal/contas`, `cmd/calibrate-argon2` com a **primeira linha real** em `argon2_calibration.jsonl`, perfil, verificação de OAB com trilha, rotas de direito do titular — e a **decisão de SMTP tomada e medida** (§15.7), que é pré-requisito, não detalhe | cadastro real funcionando, advogado verificado ≠ leigo no banco, e-mail de verificação **chegando ao Gmail**; `check-social-rate-bypass`, `check-social-sem-cors`, `check-social-cache` e `check-social-csp` verdes |
| **F2 — Conteúdo e acesso dos bots** | dúvidas, comentário jurídico com gate, feed, follows, **busca por FTS5 no SQLite social** (e o acervo por loopback em `/api/v1/search` — nenhum segundo Bleve), SSE + **gêmea Markdown, sitemap próprio, entrada no MCP/A2A/lote e cache de borda para anônimo**; filtro de ingestão ligado e camadas 2–6 do anti-abuso (§15.4); varredor de retenção por timer | primeiro conteúdo de terceiro publicado, moderável **e rastreado pelos bots de alto valor** (comprovado por `check-social-bots` e pela série de borda) |
| **F3 — Contato e conexão** | mensageria nativa (canal de registro do contrato) **sobre o compartimento de sigilo de §15.5** + **classificador de caso e conexão do modo `intermediacao`**, com trilha defensiva por conexão; **push de caso para advogado ligado** | primeira conexão real registrada, com prova de que partiu do pedido do usuário; `check-sigilo-sem-texto-claro` e `check-sem-dado-pessoal-em-git` verdes |
| **F4 — Processual** | DJEN multi-tenant por OAB, cálculo de prazo, painel do advogado; **frente DataJud (§10.2)**: destravar coleta, fila assíncrona, rate limiter 120/min, cache privado, petição ao CNJ | intimação real chegando para mais de uma OAB **e** consulta DataJud abaixo de 1 s percebido |
| **F5 — Consulta pública e ponte editorial** | **consulta processual e de jurisprudência aberta e indexável** (ato público, §2.1), sobre o corpus já existente (8.830 artigos, 2.384 precedentes STJ, 300 súmulas, Informativo STF) + thread → candidata a página v2 pelo pipeline canônico | consulta pública no ar e primeira página nascida da rede social indexada |
| **F6 — Monetização** | QR Pix estático próprio (§14.2, fase 0 — zero credencial), assinatura e cursos sob **segunda PJ comercial** (§14.4, que satisfaz o CED art. 40, IV por estrutura); pedido de autorização ao CNJ (cláusula 3.8) antes de cobrar por tela com dado DataJud | primeira cobrança conciliada, sem gateway de terceiro |

**Duas ordens dentro das fases que não são óbvias e custam caro se invertidas:**

- **A âncora do acervo entra em F2, não em F1.** O link de rodapé nas 10.141 páginas só deve
  existir quando `/redesocial/tema/…/` já responde 200 com conteúdo — publicar antes manda o
  Googlebot para uma superfície morta. E é um deploy **único**, com `--ressemear`, agrupado
  com a segunda linha `Sitemap:` no robots e com uma purga ampla só.
- **F0.5, antes de F1:** `additional_sitemap_paths` no `crawl_policy.json` e as `location`
  do nginx **sem `limit_req`**. Fazer isso antes de existir conteúdo é o que impede o
  incidente de boot da §11.1.

---

## 9. Verificação

- **Gates novos, no padrão do repo**:
  - `check-social-policy` — configuração vigente × o que o código realmente faz, com trilha.
  - `check-social-indexavel` — **o inverso do que eu havia proposto**: garante que toda rota
    pública da rede social está no sitemap, responde HTML completo sem JS, cabe em 50 KB e
    tem gêmea Markdown; e que nenhuma rota **autenticada** vaza para o índice.
  - `check-social-bots` — **prova a acessibilidade sem nunca forjar UA de bot**, que seria
    violação do anti-fraude (o hook `protect-bot-ratelimit.sh` barra, e a frase "com os UA
    dos bots… e UA próprio" que eu havia escrito era autocontraditória). Três asserções, no
    método de `check-efeito-nos-bots`: **(a)** sobre a config — `grep -c limit_req` no bloco
    `/redesocial/` = **0** (§11.2) e o mapa `$wj_bot_allow` intacto, que é o que garante a
    pista livre por construção; **(b)** sonda com **UA próprio**
    (`wikijuridica-superficie-probe/1.0` + `X-Warming-Request: true`) provando 200, HTML
    textual completo sem JS e ≤50 KB; **(c)** o comportamento real dos bots vem do **log do
    nginx**, depois do deploy, pela série de §11.8 — nunca de uma sonda que finge ser bot.
  - `check-social-csp` — CSP do `location` × hashes reais servidos.
  - `check-social-isolation` — o `cmd/server` continua respondendo com o `cmd/social` parado.
  - `check-social-cache` — requisição anônima gera HIT; requisição com cookie de sessão
    **nunca** entra no cache (o teste que impede vazamento de sessão), e o cookie se chama
    `wjsession`, com `Secure`, `Path=/` e sem `Domain`.
  - `check-social-rate-bypass` — **o inverso de `check-social-bots`**, e igualmente **sem
    forjar UA**: prova por construção que as zonas do bloco `/api/v1/redesocial/` são
    chaveadas em `$binary_remote_addr` e que o bloco não referencia `$wj_generic_key` nem
    `$wj_bot_allow`, mais uma rajada com UA próprio esperando **429** (§7.1-bis(6)). Os dois
    não conflitam — testam classes de rota opostas — e sem este o `check-social-bots`
    provaria alegremente que o buraco está aberto.
  - `check-social-sem-cors` — reprova se qualquer resposta do 8091 trouxer
    `Access-Control-Allow-Origin` (§15.6).
  - `check-moderacao-honra-exige-ordem` — prova a `CHECK` constraint **tentando o `INSERT`**
    de uma remoção por honra sem `ordem_id` (§15.1).
  - `check-promessa-privacidade-tem-substrato` — cada finalidade declarada no aviso tem linha
    em `finalidades` e código que a implemente (§15.3).
  - `check-sigilo-sem-texto-claro`, `check-sem-dado-pessoal-em-git` e
    `check-social-sem-chave-no-ambiente` — os três que tornam o compartimento de sigilo
    verificável em CI em vez de confiado à disciplina (§15.5).
  - `check-ponte-editorial-sem-autoria` — nenhum `intent_id` nascido de thread carrega
    `conta_id` (§15.2).
  - `check-edge-redirect-drift` — hoje **não existe gate nenhum** lendo
    `dynamic-redirect-rules.json` (§12.1).
- **Testes focados** por pacote, com `./tools/go-modern test -count=1 ./internal/<pkg>/` —
  nunca full-tree.
- **Smoke HTTP** ampliado: `/redesocial/` responde, o acervo continua respondendo, o canal
  de máquina continua respondendo — os três no mesmo passo.
- **Medição de regressão do ativo**: `tools/check-efeito-nos-bots` antes e depois de cada
  fase; queda de rastreio é defeito de engenharia (R6), não "depende do bot".
- **Crítica adversarial** (`Agent` com `model: fable`) antes de F1 e antes de F6 — as duas
  fases caras de reverter.

---

## 10. Decisões tomadas

### 10.1 Decisão do dono, 2026-09-04: modo `intermediacao` nasce ligado

Apresentados os três modos com o risco medido de cada um, o dono escolheu **intermediação
ativa** — matching, indicação personalizada e distribuição de caso. A decisão é dele, foi
tomada com a evidência à vista (TED/OAB-SP 25.0886.2024.023887-5) e o risco disciplinar
recai sobre a inscrição OAB/RJ 227191. Fica registrada aqui e no
`docs/goal/MAESTRO_CODEX_LOG.md`.

O que isso muda no código: `internal/socialpolicy` nasce com `modo: "intermediacao"`, e o
classificador de caso + o mecanismo de conexão entram como entrega de F3, não como código
morto atrás de flag.

**Correção registrada (2026-09-04).** Eu havia listado "push de caso para advogados" como
vedação inegociável, invocando o CED art. 40, VI. **Estava errado**: o dispositivo veda mala
direta *"com o intuito de captação de clientela"* — a conduta protegida é a do **potencial
cliente** sendo abordado. Notificar **advogados inscritos** de que há caso disponível tem
como destinatário o profissional, não o leigo; não é o ato que a norma nomeia, e o mercado
opera assim. **A trava sai. O push para advogado é funcionalidade de F3.** Permanece
distinto — e aí sim sensível — o push dirigido ao **leigo** ("o advogado X quer seu caso"),
que é abordagem ao potencial cliente.

**Nada mais fica travado.** O que sobrava como "padrão meu" vira **chave de configuração**
em `internal/socialpolicy`, sem gate que impeça ligar. Registro a base de cada uma para que
a escolha seja informada — e a escolha é sua, não minha:

| Chave | Padrão inicial | Base invocável contra | Quão literal |
|---|---|---|---|
| `push_caso_para_advogado` | **ligado** | — (a vedação de mala direta protege o cliente, não o profissional) | não se aplica |
| `intermediacao_ativa` | **ligado** (§10.1) | TED/OAB-SP 25.0886.2024.023887-5 | orientação administrativa, não lei; enforcement seletivo |
| `consulta_processual_publica` | **ligado** | — (ato público, §2.1) | não se aplica |
| `destaque_pago` | configurável | Prov. 205 art. 5º (pagar por "rankings, prêmios ou honrarias") | **analogia** — o artigo mira anuário e prêmio editorial, não posição em plataforma |
| `percentual_sobre_honorario` | configurável | CED arts. 5º/7º (mercantilização) | **inferência** — nenhum artigo nomeia plataforma; a assinatura SaaS entrega receita equivalente sem a discussão |
| `ordenacao_por_conversao` | configurável | CED art. 39 (publicidade informativa) | **boa prática**, não vedação nomeada |
| `honorario_no_perfil` | desligado | Prov. 205 art. 3º (veda "referência a honorários/descontos") | **literal** — é a única aqui que a norma nomeia diretamente |

O papel de `internal/socialpolicy` **não é impedir**: é registrar qual configuração estava
vigente em cada momento, com trilha datada. Se algum dia houver questionamento, existe prova
de o que o sistema fazia e quando — que é exatamente o que faltou às plataformas que
apanharam. Conformidade aqui é **evidência**, não freio.

**Fato de mercado que sustenta a decisão:** o Jusbrasil é empresa privada, faz intermediação
ativa há mais de uma década, tem ~20 milhões de usuários/mês, e nunca foi impedido de
operar. A OAB litigou contra plataforma menor e **perdeu** o efeito suspensivo no TRF-2.

O modo `intermediacao` também eleva o peso de dois módulos já previstos: a **verificação de
OAB passa a ser bloqueante de verdade** (conectar um usuário a alguém não verificado é o
pior caso possível), e a **trilha de auditoria** de cada conexão passa a ser prova
defensiva — quem pediu, quando, com que critério, e que o sistema não empurrou.

### 10.2 Ordem do dono, 2026-09-04: consertar e otimizar o DataJud

O DataJud deixa de ser fonte "bloqueada e evitada" e vira **frente de engenharia**. O que
isso significa concretamente, à luz do que foi medido:

**Medição própria, feita agora contra a API real** (não relato de terceiro). Consultei o
mesmo processo que o DJEN devolveu — `POST /api_publica_tjrj/_search` com query DSL do
Elasticsearch, header `Authorization: APIKey <chave pública>`:

| Medida | Valor | Consequência |
|---|---|---|
| `took` | **28.289 ms** | 28 segundos **do lado do CNJ**. Dobro dos 13,5 s registrados no ledger. Não é a nossa rede |
| `dataHoraUltimaAtualizacao` | `2026-07-24` | **lag de 42 dias** neste processo — acima da faixa de 6-41 dias já documentada. Confirma: DataJud **não** serve para prazo |
| `nivelSigilo` | `0`, no próprio registro | **achado novo**: a API entrega o nível de sigilo. O filtro de processo sigiloso pode ser **estrutural**, não heurístico |
| Estrutura | `movimentos[]` com código, dataHora, nome e complementos tabelados; `orgaoJulgador` com código IBGE; `classe`, `sistema`, `formato` | rico para histórico e para estatística; pobre para prazo (sem partes, sem íntegra) |

1. **Primeiro a fila, o cache e o limitador — só então a coleta.** A ordem importa e é o
   inverso do intuitivo: com **28 s medidos no `took`**, destravar o caminho vivo antes de
   existir fila é ligar um cliente que **bloqueia**. Então nasce primeiro: fila assíncrona,
   pré-busca em background dos processos que o advogado já acompanha (que vêm do DJEN),
   cache privado por número CNJ, e a tela mostrando o que já tem enquanto o resto chega. O
   usuário nunca espera pelo CNJ, e qualquer desenho que consulte o DataJud durante a
   renderização está quebrado por construção.
2. **Destravar a coleta real, depois.** Hoje 385 de 387 observações estão
   `planned_blocked_no_live_fetch` — o pipeline foi construído e nunca soltou. Ligar o
   caminho vivo em `internal/datajudtpubatch/executor.go`, com evidência por chamada, **por
   dentro da fila do item 1**, nunca em chamada direta.
3. **Usar `nivelSigilo` como filtro estrutural**: registro com `nivelSigilo > 0` não entra
   em superfície pública, decidido pelo dado do próprio CNJ e não por inferência nossa.
   Isso complementa `internal/publicidadenome` em vez de duplicá-lo.
4. **Rate limiter real de 120 req/min** (cláusula 3.13), global ao processo, com
   `sony/gobreaker/v2` (já no `go.mod`) e backoff — não um `time.Sleep` otimista.
5. **Resolver a cláusula 3.3/3.8 pela porta da frente.** O termo v1.2 restringe uso
   comercial, e o portal tem CTA. A rota certa não é contornar: é **redigir e enviar o
   pedido de autorização escrita ao CNJ** — é uma petição, o dono é advogado, e isso é
   trabalho que eu produzo. Até a resposta, o uso fica no que já é defensável: agregado,
   sem dado pessoal, e consulta individual restrita ao advogado sobre processo em que atua.
6. **Fechar o parecer pendente da Fase 3.3** que `docs/data-sources/FONTES_DIARIAS.md:81`
   exige e que os 283.415.422 processos agregados de 2026-08-07 já anteciparam.
7. **Manter o lag honesto na interface.** 42 dias medidos por mim neste processo. O DJEN continua sendo a
   espinha do prazo; o DataJud é histórico e metadado. A tela diz qual é qual — fingir
   tempo real com dado de 23 dias é o tipo de mentira que este contrato proíbe.

### 10.3 Correções vindas da crítica adversarial (verificadas por mim no disco)

Um agente adversarial tentou derrubar a arquitetura. Quatro achados procedem e mudam o
desenho; um estava errado, e é onde eu teria me machucado se aceitasse.

**C1 — P0. A CSP própria reprova em dois testes existentes.**
`internal/httpserver/nginx_security_header_drift_test.go` faz `filepath.WalkDir` em **`ops/`
inteiro**, recolhe **todo** `.conf` e exige que cada `Content-Security-Policy` seja
**idêntica à constante Go** `ContentSecurityPolicy`. Verifiquei a função `nginxConfFiles` —
é exatamente isso. E `security_headers_test.go:148-153` compara `script-src` por **igualdade
de conjunto**: um segundo hash reprova do lado Go também.

→ Meu §7.1-ter estava errado ao supor que bastava emitir CSP no `location`. **A correção é na
guarda, com teste** — que é o que o contrato manda (§"hook que bloqueou não se desliga:
corrige-se a causa"): o teste de drift passa a conhecer **duas** constantes Go —
`ContentSecurityPolicy` (acervo) e `ContentSecurityPolicySocial` — e a casar cada `.conf`
com a que lhe corresponde pelo `location`. Nunca por regex frouxa: o crítico notou que a
regex atual só casa aspas duplas, e usar aspas simples passaria em silêncio — isso seria
contornar o gate, que é fraude operacional. **O conserto endurece a guarda, não a afrouxa.**

**C2 — P0. A Cloudflare cacheia `/redesocial/` por padrão.** Verifiquei:
`ops/cloudflare/cache-rules.json` exclui `/buscar/`, `/contato/`, `/healthz`, `/readyz`,
`/livez`, `/metrics`, `/api/`, `/mcp`, `/a2a` e o agent-card — **`/redesocial/` não está
lá**. Eu tratei só o cache do nginx e esqueci a borda. Um GET autenticado sem
`Cache-Control` explícito seria guardado na borda por até 120 min e servido a outro
visitante.

→ Duas medidas, ambas obrigatórias: (a) acrescentar a exclusão em `cache-rules.json` e
aplicar por `tools/apply-cache-rules` — `tools/check-cache-rule-viva` passa a cobrar; (b)
`Cache-Control: private, no-store` em **toda** resposta autenticada, inclusive erro. O gate
`check-social-cache` (§9) cobre os dois.

**C3 — P0 da funcionalidade, mas o crítico errou metade. Medi eu mesmo, contra a API real.**

O crítico baseou-se em relato de integrador. Sondei o endpoint com UA próprio e header de
aquecimento, usando a OAB do dono (dado dele):

| Consulta | Resultado medido |
|---|---|
| `numeroOab=227191&ufOab=RJ&itensPorPagina=5` | `status:success` · **count=121** · items=5 |
| `numeroOab=227191-O&ufOab=RJ` | `status:success` · **count=0** · items=0 |
| `itensPorPagina=100` | `count=121` · **items=100** — funciona |
| `itensPorPagina=200` | `count=121` · **items=121** — funciona |

**Refutado:** "acima de 50 devolve vazio" **não se reproduz** — 100 e 200 devolvem tudo.
Paginação não precisa ser travada em 50.

**Confirmado, e é pior do que o crítico descreveu:** o sufixo importa, e o erro é **mudo**.
`227191-O` devolve `status: "success"` com `count: 0` — **indistinguível de "este advogado
não tem intimações"**. Não há erro, não há aviso, não há código diferente. Um cliente que
consulte a variante errada conclui "nada pendente" e o advogado perde o prazo.

**E a sondagem seguinte resolveu o problema por outro caminho — melhor.** Testei mais três
formas de consulta:

| Consulta | Resultado medido |
|---|---|
| `numeroProcesso=08012445020228190067` (sem máscara) | `count=6` · items=6 |
| `numeroProcesso=0801244-50.2022.8.19.0067` (com máscara) | `count=6` · items=6 — **aceita as duas formas** |
| `siglaTribunal=TJRJ&dataDisponibilizacaoInicio=…&Fim=…` | **`count=10000`** (teto) — varredura por tribunal/dia funciona |
| `itensPorPagina=1` | devolveu **5** — o parâmetro é **ignorado** em valores baixos |

E os campos reais de cada item são muito mais ricos do que a documentação sugere:
`hash`, `ativo`, `data_cancelamento`, `motivo_cancelamento`, `status`, `destinatarios`,
**`destinatarioadvogados`**, `link`, `meio`, `meiocompleto`, `numeroComunicacao`,
`codigoClasse`, `nomeClasse`, `numeroprocessocommascara`.

**O achado mais grave, e ninguém o tinha: `count` NÃO é o total.** Medi:

| Consulta (TJRJ, 2026-09-03) | `count` | `items` | 1º id |
|---|---|---|---|
| sem `itensPorPagina` | 100 | 100 | 713779953 |
| `&pagina=2` | 100 | 100 | 716110972 |
| `&pagina=50` | 100 | 100 | 716476554 |
| `&itensPorPagina=500` | **500** | 500 | 713779953 |
| `&pagina=2&itensPorPagina=500` | **500** | 500 | 716121949 |

**`count` é o tamanho da página devolvida, não o total do conjunto.** Ele acompanha
`itensPorPagina`. Um cliente que faça o óbvio — `if len(items) >= count: acabou` — **para na
primeira página** e perde todo o resto, sem erro, sem aviso, com `status: "success"`. Esse é
o recall silencioso de verdade, e é muito pior que a questão do sufixo: perde-se 98% das
intimações achando que a coleta terminou.

E `pagina=50` ainda devolve 100 itens novos: só o TJRJ tem **mais de 5.000 comunicações num
único dia**. Com ~90 tribunais no DJEN, a varredura diária é da ordem de **centenas de
milhares de registros** — isso é dimensionamento de infraestrutura real, não um cron
simples. `itensPorPagina=500` funciona e reduz o número de chamadas em 5×.

→ **Regra do cliente:** paginar até a página voltar **vazia** (ou com menos itens do que o
pedido), nunca confiar em `count`; `itensPorPagina=500`; e o heartbeat registra páginas
lidas e registros novos por tribunal/dia, de modo que uma coleta que pare cedo apareça como
anomalia em vez de passar por "dia tranquilo".

**Três consequências que mudam o desenho:**

1. **Coleta híbrida, com o ponto de cruzamento calculado.** A titularidade pode vir de
   `destinatarioadvogados` numa varredura por tribunal+dia, o que **elimina** o problema do
   sufixo — não importa como o tribunal grafou a inscrição. Mas varrer tudo é caro. A
   aritmética decide:

   - **por OAB**: 1 chamada por advogado (× variantes de grafia);
   - **por tribunal**: `registros_do_dia / 500` chamadas — no TJRJ, ~10 chamadas cobrem
     **todos** os advogados daquele tribunal.

   Logo o cruzamento é ~10 advogados por tribunal. **Fase 4 começa por OAB** (base pequena,
   custo mínimo, sem armazenar dado de terceiros) e **migra por tribunal** quando a base
   passar do limiar naquele tribunal — decisão automática, por medição, não por palpite. A
   consulta por OAB permanece como reconciliação em qualquer regime.
2. **`ativo` / `data_cancelamento` / `motivo_cancelamento` são P0 para prazo.** Uma
   comunicação **cancelada não gera prazo**. Um cliente que ignore esses campos calcularia
   prazo sobre intimação inexistente — e o advogado agiria com base em ato desfeito. O
   `internal/prazo` trata cancelamento antes de qualquer contagem.
3. **`hash` vem da própria API** — usar como chave de deduplicação, junto com o
   `sha256` do corpo, em vez de depender só do `id`.

**Bônus de produto:** como a consulta por `numeroProcesso` funciona sem autenticação e
aceita as duas grafias, a **consulta processual pública** (§2.2) é viável sobre o DJEN — sem
tocar no termo de uso do DataJud, que só rege a API deles.

**Terceiro achado, meu, que ninguém tinha visto:** o campo `texto` vem como **documento HTML
completo** — `<!DOCTYPE html>`, `<style>` inline, e `charset=iso-8859-1` declarado dentro de
um JSON UTF-8 com escapes. O parser precisa extrair texto de HTML e tratar essa dupla
codificação, ou o corpo da intimação chega corrompido justamente nos acentos — e é nesse
texto que mora o prazo.

**C4 — P1. A porta de ensaio do cutover é a 8090, e eu a citei trocada.**
Corrigido em 2026-09-04 por leitura da fonte: `tools/generate-nginx-standalone:34` documenta
`--porta 8090 # porta de ensaio, para o smoke do cutover`, e `ops/nginx/standalone/server.conf`
(morto) declara `listen 127.0.0.1:8090` nas linhas 15 e 244. Este parágrafo dizia 8091, e as
duas tabelas de correção mais abaixo (§12.8 e §15.7) já diziam 8090 — o plano se contradizia,
e a fonte primária resolve a favor delas.

**A escolha de 8091 para o `cmd/social` não muda**; muda a justificativa: ela não evita uma
colisão futura com o ensaio, ela evita a colisão que existiria HOJE se eu tivesse pegado a
8090. Ambas estão livres agora (`ss -ltn`).

→ **`cmd/social` usa 8091**, e a escolha entra como DEC nova no `docs/goal/DECISIONS.md`,
junto com a topologia de dois processos (DEC-022 fixou 8088/8089 e precisa ser estendida,
não contrariada em silêncio).

**C5 — P1. `cmd/social` é invisível ao `deploy-publico`.** O script tem
`SERVICE=wikijuridica-server` único, compila só `./cmd/server`, e o fingerprint de camada só
considera aquele binário — mas o ingress **é** vigiado, então a `location` nova dispararia
reload apontando para uma porta que nenhum passo sobe: **502 até alguém subir à mão**.

→ O deploy passa a conhecer os dois serviços: segundo binário, segundo fingerprint, ordem
binário→socket→serviço para ambos, e `tools/check-portal-health` ganha o segundo alvo.

**C6 — o achado que eu REJEITO, com evidência.** O crítico afirmou que
`ops/nginx/standalone/nginx.conf` é gerado a partir de `ops/nginx/wikijuridica.conf`, e que
editar o destino é trabalho perdido. **Falso hoje, e perigoso.** Li o banner do
`wikijuridica.conf`: ele declara a colisão de fonte-de-verdade em letras maiúsculas — a unit
carrega o **standalone**, o standalone está **à frente** (76 diretivas contra 67), três
commits de 2026-08-20 editaram só ele, e os testes de contrato Go o declaram canônico. O
banner é explícito: *"rodar `tools/generate-nginx-standalone` para propagá-lo REGRIDE o que
está no ar"*.

→ **Editar o `standalone/nginx.conf` diretamente é o certo. Não rodar o gerador.** Se eu
tivesse aceitado o achado do agente, teria regredido a configuração de produção — é
exatamente o caso que a regra "output de subagente é alegação até verificação própria"
existe para evitar.

**Sobre os achados jurídicos do crítico (art. 42-I, modo `intermediacao`):** ele reafirma o
risco que já está medido em §1 e §10.1. A decisão foi tomada pelo dono com essa evidência à
vista; não reabro. Fica registrado que a crítica foi feita e o risco é conhecido — que é
precisamente o valor da trilha datada.

### 10.4 Desenho técnico consolidado (do agente de conteúdo, revisado por mim)

**Bloqueador que aparece antes da primeira linha de código — e ele é 16× maior do que o
agente relatou.** O agente de conteúdo varreu estaticamente e achou "17 escapes". **Rodei o
gate de verdade** (`./tools/go-modern run ./cmd/check codex2-policy-enforcement
--max-errors 0`, exit 1) e a medição real é **273 falhas**:

| Código | Falhas | Natureza |
|---|---|---|
| `external_dependency_unapproved` | **84** | módulo no `go.mod` sem registro, ou com **versão** diferente da registrada |
| `runtime_candidate_module_unapproved` | **79** | idem, na trilha de candidato a runtime |
| `pebble_import_scope_escape` | 27 | import fora do escopo declarado |
| `bleve_import_scope_escape` | 15 | idem (o número que o agente viu) |
| `x_net_html` · `x_time_rate` · `x_text` · `robotstxt` · `approved` · `x_sync` · `hnsw` · `sqlite` · `jsonschema` · `uax29` · `grobotstxt` · `goquery` · `go-minhash` · `bloom` | 68 | idem, 14 módulos |
| `approved_evidence_invalid` | 7 | evidência de adoção que não valida |

**Causa raiz medida, e é única para as duas famílias que somam 163 (60%):** o registro de
dependências é **hardcoded em Go** (`adoptedDependencyRecord`, `policy.go:1288` e seguintes)
e fixa `AdoptedModuleVersion` literal — enquanto o `go.mod` tem **201 requires diretos** que
evoluíram desde então. Cada `go get` que subiu uma versão criou uma falha, sem ninguém
notar, porque o gate já estava vermelho. `golang.org/x/net@v0.58.0` reprova mesmo tendo
`xNetHTMLImportAllowed` — o módulo tem registro, a **versão** não bate.

**Consequência para este plano, e ela é séria:** o §10.4 propõe usar este gate como **trava
estrutural** do DataJud (`datajudImportAllowed`). Um gate com 273 falhas **não trava nada** —
ninguém lê um vermelho permanente, que é exatamente como as 273 se acumularam. Então a
sequência é: **(a)** registrar o baseline medido (273, com esta data) para que regressão nova
seja distinguível de dívida herdada; **(b)** corrigir a causa raiz das 163 — derivar o
registro do `go.mod` em vez de duplicá-lo à mão, que é a única forma de isso não voltar;
**(c)** só então estender as allowlists para `modernc.org/sqlite` em `cmd/social` e criar
`datajudImportAllowed`, reescrevendo o `DecisionReason` (hoje diz "sidecar derivado, JSONL
continua canônico", e estado social é **canônico**, não sidecar).

É frente própria, com ADR, e **não bloqueia F0** — bloqueia o momento em que o gate passa a
ser invocado como trava, que é F4.

**Uso do mesmo gate como trava estrutural — a melhor ideia do relatório.** Acrescentar
`datajudImportAllowed`, permitindo `internal/datajud` apenas em si mesmo e em `cmd/social`.
Qualquer arquivo de `internal/render`, `seo`, `sitemap*`, `publicrelease`, `pagefactory`,
`feed`, `cmd/build` ou `cmd/publish-v2-direct` que importar aquele pacote **reprova o gate**.
Resultado: dado do DataJud **não tem como** chegar a artefato público — não por política, mas
porque nenhum pacote do caminho de publicação compila contra ele.

> **SUPERADO EM 2026-09-16, por ordem do dono — o parágrafo acima fica, o regime não.** A trava
> de import foi construída como descrito e **caiu** nesta data: as duas razões escritas nela eram
> falsas. Termo de uso de API pública não revoga a publicidade constitucional do ato judicial
> (CPC art. 189; CF art. 5º LX, art. 37 *caput* e art. 93 IX; Lei 12.527/2011, art. 3º, I; Res.
> CNJ 121/2010, art. 2º, II, que nomeia o **nome das partes** entre os dados de livre acesso), e
> os 42 dias de defasagem inviabilizam **cálculo de prazo**, não página informativa — defasagem
> conhecida se **declara** na proveniência. E a trava era incoerente com o próprio projeto:
> `cmd/social/processotela.go` já servia consulta de processo do DataJud em superfície pública,
> com a guarda de conteúdo de `internal/datajudfila`.
>
> **O código de violação `codex2_policy_datajud_import_scope_escape` não sumiu: mudou de
> sentido.** Deixou de marcar *"importou"* e passou a marcar *"serviu sem filtro de sigilo ou sem
> proveniência"* — `datajudFronteiraDeSaida` cobra, por AST, que `Resposta.Sigiloso()` decida pelo
> `nivelSigilo` do CNJ, que `DetalheDaResposta` recuse o sigiloso na **primeira instrução** e que
> a fronteira carregue `FonteURL`, `CorpoSHA256` e `ServeParaPrazo`. A lista de imports era
> **proxy**; a invariante cobrada é **proteção**. O caso completo está em
> `docs/PRECEDENTES_DAS_ORDENS.md` ("A trava que reprovava a rota certa").

**Busca social: FTS5 no mesmo SQLite, não um segundo Bleve.** Elimina a classe inteira do
incidente de 2026-08-19 (segundo índice, segundo diretório, segundo `root.bolt` flockado).
Precedente já no repositório: `internal/sqlitefts5corpus` com
`tokenize='unicode61 remove_diacritics 2'` — que é o certo para PT-BR ("usucapiao" acha
"usucapião"). A busca no **acervo**, dentro da rede social, é chamada HTTP em loopback para
`/api/v1/search` no 8089: um processo, um índice, `cmd/social` como cliente e nunca como
segundo dono.

**Timeline: fan-out on read**, com a aritmética explícita — a rede nasce em zero posts e o
teto plausível do primeiro ano é ~10³ advogados. Materializar timeline para poupar um
`SELECT … JOIN follows` indexado é otimização adiantada em três ordens de grandeza. O ponto
de reversão fica **escrito no código**: quando o p95 de `FeedInicio` passar de 50 ms sobre
dado real medido por `internal/perflatencyhistogram`. Paginação por **keyset**, nunca
`OFFSET`.

**Schema**: `var/social/social.db` (posts, perfis, follows, curtidas, notificações) e
`var/social/processual.db` (intimações, titularidade, heartbeat de coleta) — arquivos
**separados**, fora de `var/on-demand-cache` (que `deploy-publico` apaga com `rm -rf` no
passo 4). Uma tabela `post` única para dúvida/resposta/blog, porque thread é árvore e três
tabelas obrigariam `UNION` para montar uma conversa. Contadores por trigger na mesma
transação, em vez de `COUNT(*)` por post no feed.

**Intimação multi-tenant**: a comunicação é **global** (a mesma intimação serve a todos os
advogados do processo) e a **titularidade** é por conta, em tabela separada — duplicar o teor
por advogado faria duas contas divergirem sobre o mesmo ato. Dedup em dois níveis:
`UNIQUE(fonte, id_externo)` para a janela de polling sobreposta, e
`UNIQUE(fonte, corpo_sha256, processo)` para republicação com id novo.

**Cálculo de prazo — a assimetria que governa o pacote.** Errar tem duas direções e elas
**não são equivalentes**: dia não-útil faltando adianta o aviso (erro seguro); dia não-útil
sobrando empurra a data para depois da real e produz protocolo **intempestivo** (erro
fatal). Portanto: **na dúvida, o dia CONTA como útil**; só sai da contagem quando um ato
oficial disser expressamente que o prazo está suspenso. Ponto facultativo e expediente
reduzido viram alerta, nunca um dia a mais. E a **classe processual** decide o regime, não o
nome da vara — existe "Juizado Especial Cível **e Criminal**", e classificar pelo órgão
contaria um processo cível em dias corridos (CPC art. 219 × CPP art. 798).

**Quatro estados distintos, nunca o mesmo vazio**: `lido` (prazo escrito no texto),
`presumido` (derivado da lei — em coluna **própria**, para não passar por data lida do
juiz), `expediente` (não abre prazo; ausência de data é o estado correto) e `sem_prazo`
(precisa de olho humano). Campo vazio que significa duas coisas opostas ensina o advogado a
ignorar justamente o caso em que o prazo já disparou.

**Ponte editorial**: candidato nasce em `data/editorial/v2_candidates/`, **fora** do glob
`v2_pages/*.jsonl` que `v2acervosimilarity.Validate` varre — senão contaria como acervo antes
de qualquer revisão. Promoção só após aprovação, e então `portfolio_v2/` **primeiro**,
`v2_pages/` **depois**, com `check-v2-portfolio-pairing` antes. Limiares medidos: ≥250
palavras (piso crítico do contrato), ≥1 dispositivo com URN que **existe** em
`legalcorpusindex`, recorrência ≥3 dúvidas distintas por MinHash/Jaccard com **3-gramas a
0,60** — porque o 5-grama deixa passar molde quando há número intercalado, defeito já medido
no projeto. Autoria pela **regra das duas camadas** do DEC-032: a resposta do advogado entra
como citação identificada (nome, inscrição, data, link), e o comentário autoral do pipeline
é o que faz a página existir.

**Divergência que corrigi.** O agente propôs `post.index_policy` travado em `'noindex'` por
`CHECK`, com cinco camadas de imposição. **Isso contraria a ordem do dono (§7.3)**: a rede
social é totalmente acessível aos bots. A coluna fica, o `CHECK` rígido sai; a política de
indexação passa a ser **derivada** (thread com resposta de verificado e conteúdo mínimo é
indexável; rascunho e área autenticada não são), e o gate `check-social-indexavel` verifica
os **dois** sentidos — que o público está no sitemap e que o autenticado não está.

### 10.5 Decisões de engenharia que tomei com dado

Processo separado (`cmd/social`), escrita sob `/api/v1/redesocial/*` por causa do WAF,
`location` com cache condicionado à sessão, duas constantes de CSP, SQLite com WAL,
render no servidor,
**busca social por FTS5 no mesmo SQLite — nenhum segundo Bleve** (e `WIKI_CACHE_DIR` próprio
como cinto de segurança), DJEN como espinha do
acompanhamento, mensageria nativa como canal de registro do contrato, WhatsApp por
`whatsmeow` como notificação desacoplada, **UGC público indexável e acessível aos bots**.

---

## 11. Achados da frente de indexação (agente de SEO/IA, verificados)

### 11.1 BLOQUEANTE — o sitemap social no índice do acervo derruba o portal

`internal/publishedmanifest/publishedmanifest.go:546-577` (`indexedPublicSitemapShardName`)
exige que **todo `<loc>` de `public/sitemap.xml`** tenha prefixo `/sitemaps/` e sufixo
`.xml`. Um `<loc>` para `/redesocial/sitemap.xml` produz
`published_manifest_sitemap_missing`, que **não** está em `staticArtifactOnlyIssueCodes` —
logo entra em `BootBlockingIssues` e `httpserver.New` devolve erro. **O `cmd/server` não
sobe**, e caem junto MCP, A2A, as gêmeas Markdown e `/api/v1/*`.

E a alternativa ingênua é pior: escrever o sitemap social em `public/sitemaps/` faz cada
`<loc>` social exigir registro no `published_manifest`, disparando
`published_manifest_sitemap_loc_without_manifest` — que o comentário do arquivo declara
**deliberadamente fatal** ("sinal de corrupção de pipeline").

→ **Descoberta por segunda diretiva `Sitemap:` no `robots.txt`.** Hoje `internal/crawl`
escreve exatamente uma, derivada de `policy.SitemapPath` (string única). Vira
`sitemap_path` + `additional_sitemap_paths []string` em `content/crawl_policy.json`, com a
validação análoga e ajuste em `crawl_test.go` e `tools/check-public-robots-drift`. ~30
linhas que evitam indisponibilidade total do canal de máquina.

### 11.2 Correção: `limit_req` está no `server{}`, não no `http{}`

Meu §7.3 afirmou que as `location` novas herdam o rate limit "por estarem no nível
`http{}`". O resultado é o certo, o mecanismo não: as cinco `limit_req` estão no `server{}`
(`wikijuridica.conf:785-789`); só as `limit_req_zone` e os `map` estão no `http{}`. E a
herança do nginx é **tudo-ou-nada**: uma `limit_req` declarada dentro da `location` nova
**substitui as cinco**, incluindo `wj_generic` — e o Googlebot passaria a ser limitado em
silêncio.

→ Regra: `location ^~ /redesocial/` **sem nenhuma `limit_req`**. O gate `check-social-bots`
prova pelo lado negativo: `grep -c limit_req` dentro do bloco = 0.

### 11.3 O QAPage foi retirado do acervo por inelegibilidade que a rede social não tem

`internal/structureddata/structured_data.go:406-418` registra a retirada de 2026-08-20, em
441 páginas, citando a diretriz do Google: não usar `QAPage` quando há **uma só resposta,
escrita pelo próprio site, sem submissão de usuário**. A rede social é exatamente o caso
elegível que faltava: pergunta de terceiro, respostas de terceiros, `answerCount` real.
Os sete campos que o Search Console apontava como ausentes (`author`, `datePublished`,
`upvoteCount`, `url`) **existem de verdade** aqui.

É o **único rich result que este domínio pode legitimamente ganhar**, e sai de graça.
A guarda incondicional de `:612-619` vira condicional — aceita `QAPage` quando há
`answerCount ≥ 1`, resposta aceita ou sugerida, e `Answer.author` é `Person` distinta do
site; fora disso continua reprovando.

Duas regras da diretriz que decidem arquitetura: **uma pergunta por página** (feed e tema
usam `CollectionPage`, nunca `QAPage`), e **`DiscussionForumPosting` é vedado a conteúdo do
próprio publisher** — post do dono é `Article`, não `DiscussionForumPosting`. Vira asserção
do gate, cruzando `author.@id` com a identidade de `content/site.json`.

### 11.4 O piso de conteúdo, medido no acervo real

Cálculo sobre `content/pages.json` (10.148 páginas indexáveis): corpo **mínimo 1.111
caracteres**, P10 = **1.936**, P50 = 2.973. O acervo não tem nenhuma página indexável abaixo
de 1.111.

→ Piso social: **≥1.100 caracteres** somando pergunta + respostas publicadas. Não é palpite —
é "a página social mais magra não pode ser mais magra que a de acervo mais magra". Thread com
zero respostas fica `noindex` (a própria diretriz do QAPage diz que pergunta sem resposta é
inelegível). Quase-duplicata usa o limiar **que o repositório já usa**: Jaccard 0,70
(`v2bodyneardup.DefaultThreshold`), densidade de repetição 0,15. O gate
`check-social-conteudo-fino` é **comparativo**: reprova se o P10 social cair abaixo do P10 do
acervo, de modo que o piso acompanhe o acervo em vez de envelhecer.

### 11.5 Feed e IndexNow — dois erros caros evitados

**O `/feed.xml` tem 1.000 entradas.** UGC nele expulsaria o acervo inteiro da janela em
poucos dias, e o hub WebSub passaria a empurrar só conteúdo social aos assinantes.
→ **`/redesocial/feed.xml` separado**, tópico WebSub próprio. O feed do acervo não é tocado.

**IndexNow: o muro é granularidade, não volume.** Um POST com 10.000 URLs custa o mesmo em
ledger que um POST com 1 URL (`MaxEvidenceRecords = 100000`, 2 registros por wave).
Submeter post a post esgotaria em semanas o ledger da vida inteira; em lote horário, são 48
registros/dia e o ledger dura **~5,7 anos**.
→ Submissão **por transição de indexabilidade**, não por evento de escrita: a primeira
resposta que cruza o piso submete; curtida e view nunca; remoção por moderação submete
imediato (é o único caso urgente). Fila drenada de hora em hora, num POST.

### 11.6 `lastmod` causal — a lição já medida no acervo

`internal/sitemap/carencia_lastmod.go:20-26` registra o caso: 28 shards em carência
anunciaram 8.436 URLs com `lastmod` mais novo que o plano vivo — "um pedido de re-rastreio de
8.436 URLs que não mudaram". Numa rede social esse erro é diário.

→ `lastmod` muda **apenas** com o que muda o HTML servido: resposta nova, edição, remoção.
**Nunca** com visualização, curtida, contador ou ordenação. Se o contador aparece no HTML,
ele sai do HTML. `check-social-lastmod-causal` compara `lastmod` × hash do corpo servido em
amostra e reprova divergência.

**Shard por chave estável, nunca ordinal posicional.** O acervo mantém hoje **31 shards de
carência para 48 vivos** — 39% dos arquivos existem só para não dar 404, porque o ordinal
`pages-%04d.xml` muda quando o plano encolhe. Na rede social, shard por mês de criação
(`duvidas-2026-09.xml`) e bucket imutável de perfil: o conjunto **só cresce**, e
`sitemapgrace` nunca precisa ser acionado — não por burla, mas porque a causa não existe.

### 11.7 Canal de máquina: `cmd/server` lê o SQLite social em modo somente-leitura

O conteúdo social vive no `cmd/social`, mas `/mcp`, `/api/v1/lote` e os descritores vivem no
`cmd/server`. Três caminhos, e um é impossível: hospedar `/redesocial/mcp` no `cmd/social`
partiria a superfície de agente em dois servidores MCP — e o WAF só deixaria passar
`/api/v1/redesocial/mcp`, contrariando `agentsurface` ser fonte única. Proxy por loopback
recriaria o acoplamento que o processo separado comprou.

→ **`cmd/server` abre o SQLite social com `?mode=ro`.** WAL admite leitores concorrentes com
um escritor. E o padrão de **fail-open por capacidade armada já existe e é testado** em
`mcp.go:341-349`: `relatar_defeito` só é registrada quando as duas dependências existem,
"porque registrar com um dos dois nil anunciaria em `tools/list` uma capacidade que toda
chamada real recusaria". Mesma mecânica: arquivo ausente ou corrompido ⇒ as ferramentas
sociais não são registradas, o acervo segue intacto — e é isso que `check-social-isolation`
prova, derrubando o `cmd/social` e conferindo que `/mcp` continua servindo o acervo.

Quatro ferramentas novas em `mcp_social.go`: `buscar_duvidas`, `ler_duvida`,
`perfil_de_jurista`, `duvidas_do_tema`. **`buscar_duvidas` consulta o FTS5 do próprio SQLite
social pela mesma conexão `?mode=ro` — não existe índice Bleve social** (§6.5, §10.4), e
quem implementar não deve criar um. A segunda devolve **byte a byte** a gêmea `.md`,
como `ler_pagina` faz — nenhuma representação nova nasce. E cada ferramenta nova obriga
linha no `/auth.md` (há teste que compara o texto contra o `tools/list` vivo) e no
`server-card.json`.

**`/api/v1/redesocial/lote`** como canal irmão, não mistura: o cursor do `/api/v1/lote`
resolve o índice **uma vez no boot**, o que é incompatível com conteúdo que muda a cada
minuto. Mesmo contrato de forma (NDJSON, linha final `{"tipo":"fim"}` — sem ela um stream
cortado é indistinguível de um completo), tetos 50/200, ordenação por `lastmod` crescente.

### 11.8 Medir crescimento × canibalização — o discriminador

O orçamento de rastreio é finito. A série nova `data/ops/social_bot_coverage_daily.jsonl`
ganha o campo **`superficie`** (`acervo` | `redesocial`) — é essa coluna que separa os três
estados:

| Acervo | Rede social | Leitura | Ação |
|---|---|---|---|
| ↑ ou = | ↑ | **crescimento real** — o domínio ganhou orçamento | seguir |
| ↓ | ↑ | **canibalização** — o mesmo orçamento foi realocado | subir o piso, apertar `lastmod`, tirar thread fina do sitemap |
| ↓ | ↓ | regressão de infraestrutura, não de conteúdo | borda, WAF, `check-superficie-bots-live` |

Sinal secundário e mais honesto: requisições **por URL indexável**, por superfície. Se o
acervo cai em absoluto mas mantém requisições/URL, o domínio cresceu e o acervo só perdeu
participação — que não é o mesmo defeito, e um gate que confunda os dois manda apertar o
parafuso errado.

O gate copia inteiro o método de `tools/check-efeito-nos-bots`: dado do **log do nginx**
(nunca do ledger do Go — o acervo é estático e não chega ao processo), janelas PRÉ/PÓS de 14
dias com N≥100, autenticação por **faixa de IP oficial** (há medição de scanner entrando com
`allow=1` por forjar UA de bot valioso, inclusive ClaudeBot), e limiares **hardcoded** —
expô-los na linha de comando é o caminho mais curto para afrouxar até passar.

---

## 12. Fundação e identidade (F0/F1) — desenho verificado

O agente que produziu esta parte foi briefado antes das suas decisões de 2026-09-04. Integro
o que ele **mediu**; corrijo o que ficou desatualizado (porta, indexação, travas) conforme
§0.2, §7.3 e §10.1.

### 12.1 Três achados de infraestrutura que evitam incidente

**A base de contas nasceria sem backup.** `tools/generate-backup-wiki:43` exclui `var/` por
construção ("regenerável") — e é exatamente onde o SQLite social vai morar. Correção: bloco
novo no backup, no mesmo espírito do que já existe para `.env.local` ("fora do git por
desenho, mas sole-copy"). E **`VACUUM INTO`, nunca `cp`**: com WAL ligado, o `.db` sozinho é
uma foto anterior ao último checkpoint, e copiar `.db` + `-wal` + `-shm` em três instantes
produz um arquivo que **abre e mente** — a pior forma de backup que existe.
`tools/check-backup-restauravel` ganha `PRAGMA integrity_check` + `foreign_key_check`.

**Trava de borda nº 5, que ninguém tinha visto: o Dynamic Redirect quebra os assets.**
`ops/cloudflare/dynamic-redirect-rules.json` acrescenta barra final a todo path que não
termine em `/`, excluindo apenas `.txt .xml .md .json .ico .png .svg .webmanifest .html`.
Logo `.css`, `.js`, `.woff2` e `.webp` levam **301 na borda**:
`/redesocial/assets/rs-abc.css` → `/redesocial/assets/rs-abc.css/`. A folha morre com a
`location` do nginx perfeitamente correta, e o sintoma (página sem estilo) não aponta para a
causa. Correção estreita: excluir `/redesocial/assets/` da expressão — nunca acrescentar
`.css`/`.js` à lista global, que mudaria o site inteiro.
**E não existe gate nenhum lendo esse arquivo** (`grep -rln dynamic-redirect-rules.json
tools/` → vazio): há drift para WAF e para cache rules, nada para redirects. Nasce
`tools/check-edge-redirect-drift`.

**O teste de drift da CSP se resolve pinando por arquivo — e fica mais estrito.** Em vez de
aceitar um *conjunto* de valores (o que deixaria passar uma CSP trocada entre acervo e rede
social), o teste ganha `cspEsperadaPorArquivo(base string)`, que devolve
`socialheaders.ContentSecurityPolicy` para `redesocial-headers.conf` e a do acervo para o
resto. O import do pacote novo fica **só no `_test.go`**, então `go list -deps ./cmd/server`
continua sem nada de social — e é isso que `social-isolation` verifica.

### 12.2 Segurança de conta — parâmetros concretos

- **Argon2id com `m=65536 KiB (64 MiB), t=3, p=2`** — e o `p=2` é escolha de **hardware
  medido**, não cópia de recomendação. A máquina é um i7-8565U: 4 núcleos / 8 threads,
  1,8 GHz base, peça ULV de notebook, com load 1,91 / 1,99 / 1,85 **antes** de a rede social
  existir (nginx + `cmd/server` + 46 timers já residentes). Um hash que tomasse 4 lanes
  disputaria CPU com os workers do nginx e com o caminho de requisição do `cmd/server` — e
  degradar o acervo é regressão P0 (R6). Como o custo do Argon2 é dominado por `m × t`,
  baixar `p` custa quase nada em força e devolve muito em latência do vizinho; `t=3`
  compensa. 64 MiB é o segundo perfil do RFC 9106 e é o número que torna paralelismo em GPU
  caro. Formato PHC completo no banco
  (`$argon2id$v=19$m=65536,t=3,p=2$<sal>$<hash>`), para que subir parâmetros vire
  rehash-no-login e não migração cega. Assinatura verificada em
  `x/crypto@v0.55.0/argon2/argon2.go:101`.
- **Os números acima são ponto de partida, e são rotulados ASSUMIDO até serem medidos.**
  `cmd/calibrate-argon2` grava `data/ops/argon2_calibration.jsonl` com
  `medido_em, m_kib, t, p, load1, p50_ms, p95_ms, concorrencia`; **banda de aceitação de
  150–400 ms de p50 sob load ≈ 2,0**. Fora da banda, `t` se move primeiro (alavanca mais
  barata), depois `m`. R3 não admite parâmetro de segurança escolhido por citação.
- **Semáforo de 4 hashes concorrentes, e a aritmética muda a unit.** 4 × 64 MiB = **256 MiB
  transitórios de heap** — contra os `MemoryMax=512M` que eu havia escrito, sobrariam ~150
  MiB para SQLite, render e sessões, com o cgroup matando (hard) antes de o `GOMEMLIMIT`
  (soft) apertar o GC. Então a unit sobe para **`MemoryMax=768M` / `GOMEMLIMIT=600MiB`**
  (§12.6): a máquina tem 14,5 GB disponíveis, o teto baixo existia para não competir com o
  acervo — e o `OOMScoreAdjust=-100` já garante que a rede social morra primeiro, que é a
  proteção que realmente importa. Sem o semáforo, 100 logins concorrentes seriam 6,4 GB e a
  máquina iria para o swap — desastre de desempenho **e de segurança**, porque estado de
  hash em disco é material de chave em disco.
- **Cookie `wjsession`** — e aqui eu tinha errado ao propor `__Host-rs_sessao`. Existe razão
  técnica dura: **`$cookie_<nome>` do nginx só aceita `[A-Za-z0-9_]`**, então um prefixo
  `__Host-` obrigaria a substituir o `proxy_cache_bypass $cookie_wjsession` por um
  `map $http_cookie` com regex — mais frágil, no caminho que impede vazamento de sessão pelo
  cache. O nome fica `wjsession`, e as três propriedades que o prefixo daria de graça
  (`Secure`, `Path=/`, sem `Domain`) viram asserção do gate `check-social-cache`, que já
  inspeciona esse cookie de qualquer forma. `SameSite=Lax` — e não `Strict` — porque um link
  do acervo para rota logada precisa manter a sessão, e `Lax` já barra POST cross-site.
- **`sessao_geracao INTEGER NOT NULL DEFAULT 1`** na conta, comparada a cada requisição.
  Troca de senha, "sair de todos os dispositivos" e suspensão por moderação a incrementam:
  **um inteiro derruba todos os dispositivos sem varrer tabela**, e é a mesma primitiva que
  faz suspensão por moderação ter efeito instantâneo.
- **Expiração dupla:** absoluta de 30 dias e inatividade deslizante de 12 h (um dia útil) —
  a ameaça realista é o navegador do profissional numa máquina compartilhada de escritório.
- No banco só o `sha256` do id; o id vivo existe apenas no cookie. Dump do banco não devolve
  sessão a ninguém. Rotação em login, troca de senha, confirmação e mudança de estado.
- **Anti-enumeração**: `ConfereFalso` roda o mesmo custo Argon2id contra hash sentinela
  quando a conta não existe — sem isso o tempo de resposta enumera contas cadastradas.
- Senha: mínimo 12 caracteres, lista de senhas comuns embarcada, **sem** regra de composição
  (NIST SP 800-63B: regras de composição pioram a entropia real).

### 12.3 Confirmação de e-mail em dois passos — e o estado real da máquina

**Medido:** `msmtp 1.8.23` está instalado como `/usr/sbin/sendmail`, **sem** `/etc/msmtprc`
nem `~/.msmtprc`, e **nada escuta em :25 ou :587**. Não há `net/smtp` no repositório.

Desenho: **fila primeiro** — todo e-mail vira linha em `email_saida` na mesma transação que
cria a conta/token, com recuo exponencial. Transporte por `/usr/sbin/sendmail -t -i`. Sem
MTA no ar, nada se perde e o usuário não vê erro por causa do correio.

**Dois passos, e não é preciosismo:** varredores corporativos de link (Safe Links e
equivalentes) seguem todo GET de e-mail. Se o GET consumisse o token, o varredor queimaria a
confirmação antes de o humano abrir a mensagem, e o suporte veria "o link não funciona" sem
causa visível. Então: `GET /redesocial/confirmar/?t=…` **renderiza um botão**;
`POST /api/v1/redesocial/confirmar` consome.

**Bloqueante de ops, declarado:** sem `/etc/msmtprc` e sem SPF, DKIM e DMARC publicados no
DNS, a entrega é ~0% e a confirmação não chega. Isso está no checklist de deploy de F1, não
numa fila de "depois".

### 12.4 O que o schema impede por ausência

A trava mais forte não é `CHECK`, é **não existir onde gravar**. O schema não tem coluna de
`honorario`, `preco`, `nota`, `avaliacao`, `estrela`, `conversao`, `lead` — e o gate
`social-policy` varre o DDL por esses radicais. As colunas de `destaque`/`ranking`/`plano`
**existem** (§10.1 as tornou configuráveis), mas o valor vigente fica registrado com trilha
datada.

`email_saida.template` tem `CHECK` com conjunto fechado (`confirmacao`, `recuperacao`,
`verificacao_deferida`, `verificacao_recusada`, `decisao_moderacao`) e `internal/socialmail`
não expõe função que aceite corpo livre. Consequência: **mala direta a coletividade é
impossível de gravar** — o que continua correto mesmo com o push de caso liberado, porque
push de caso é notificação a profissional inscrito, dentro do produto, e não disparo de
publicidade a uma lista.

**Anti-squatting da OAB**: a linha em `perfis_advogado` (com `UNIQUE(oab_numero, seccional)`)
só nasce quando a verificação é **deferida**. Se o único índice valesse desde o pedido, quem
chegasse primeiro com um número alheio bloquearia o titular até a recusa.

**Enum de conteúdo já inclui `duvida` e `resposta`** mesmo sem F1 escrevê-los: trocar um
`CHECK` no SQLite exige reconstruir a tabela, e reconstruir tabela de moderação com denúncias
vivas é risco maior do que declarar hoje o enum que F2 usará.

### 12.5 Cifra em repouso — com o limite dito

`SQLCipher não existe sob modernc.org/sqlite` (é transpilação do SQLite upstream, que não
tem cifra embutida). Logo: **cifra por campo**, AES-256-GCM, nonce por registro, AAD =
`tabela||coluna||id`, KEK em `WIKI_SOCIAL_KEK` no `.env.local` (que o `EnvironmentFile=-` já
lê e o backup já trata como segredo).

Cifrados: e-mail da conta, evidência da verificação, denunciante, IP de registro de acesso,
destinatário de e-mail. **Não** cifrados, com motivo: hashes de senha/sessão/CSRF já são
unidirecionais; `conteudos.texto` é público por natureza; `perfis_advogado` é público **por
dever** (CED art. 44).

**Índice cego** para o e-mail: `HMAC-SHA256`, não SHA puro — permite login e "já cadastrado"
sem decifrar, e um dump sem a chave não abre dicionário sobre endereços.

**Limite honesto:** cifra por campo protege **arquivo roubado**, não **processo
comprometido** — a KEK está na memória do `cmd/social`.

**E há um regime que esta seção NÃO cobre, corrigido em §15.5.** Tudo acima vale para dado
**operacional**, que a plataforma precisa ler para funcionar (e-mail, evidência de
verificação, registro de acesso) — e para esse, KEK no ambiente é adequado. O **conteúdo de
caso e a conversa cliente-advogado são regime oposto**: se a chave estiver no ambiente, todo
agente, todo timer e todo backup a leem, e a violação de sigilo do EOAB art. 34, VII vira
questão de tempo. Lá a chave é derivada da **senha do participante** e **não existe chave que
o operador tenha**.

### 12.6 A unit que materializa o isolamento em número

```
OOMScoreAdjust=-100     # contra -500 do cmd/server
MemoryMax=768M
Environment=GOMEMLIMIT=600MiB
```

O teto subiu de 512M pela aritmética do Argon2id (§12.2): 4 hashes concorrentes × 64 MiB =
256 MiB transitórios, e com 512M o cgroup mataria (hard) antes de o `GOMEMLIMIT` (soft)
apertar o GC. A máquina tem 14,5 GB disponíveis; o teto baixo existia para não competir com
o acervo, e essa proteção continua inteira no `OOMScoreAdjust`.

O `-100` é a decisão **oposta** à do `cmd/server`, e de propósito: na falta de memória o
kernel escolhe **este** processo primeiro. A rede social morre antes do canal de máquina,
nunca depois. E `GOMEMLIMIT` anda com `MemoryMax` sempre — sem ele o GC do Go não conhece o
teto, o cgroup mata antes de o coletor ficar agressivo, e o `Restart=always` transforma isso
em laço justamente sob carga de login.

`Requires=wikijuridica-social.socket`, `Type=notify`, e o pacote novo
`internal/sdactivation` com **teste de paridade que lê `cmd/server/main.go` por AST** —
porque o custo de errar já está medido: 1.435 respostas 502 em 26–28/08/2026, por binário
que fazia bind próprio em vez de adotar o socket.

### 12.7 `html/template`, não concatenação

O acervo usa `html.EscapeString` porque o conteúdo é editorial revisado. **UGC concatenado é
fábrica de XSS.** `html/template` faz escape **contextual** (atributo, URL, JS), é stdlib, e
não colide com `architecture.forbiddenFrontendTokens` (que proíbe react/vue/svelte/next).
Zero JavaScript em F1 — formulários HTML puros, o que permite `script-src 'none'` e dispensa
toda a derivação de hash de script.

### 12.8 Correções que apliquei ao relatório

| O agente propôs | Corrigido para | Por quê |
|---|---|---|
| porta **8090** | **8091** | 8090 é a porta de ensaio do cutover do nginx (§10.3, C4) |
| `X-Robots-Tag: noindex` em **toda** resposta | `noindex` **apenas** em rota autenticada | §7.3 — a rede social é acessível aos bots |
| `modos_habilitados: ["diretorio"]` | `["intermediacao"]` | §10.1, sua decisão |
| Proibições `true` obrigatórias, JSON incapaz de expressar valor permissivo | chaves configuráveis com trilha datada | §10.1 |
| `intermediacao` nasce desligada, exige arquivo de decisão | nasce **ligada**; o arquivo de decisão registra **quando e por quem** | §10.1 |

**O que mantive integralmente** porque não é trava de produto e sim regra literal: nenhum
`Disallow: /redesocial/` no robots.txt — `Disallow` impede o **rastreio** e portanto impede
que o `noindex` da área autenticada seja **lido**, deixando a URL indexável por link externo
com o rótulo "nenhuma informação disponível". A trava correta é sempre o header.

### 12.9 Colisão que é decisão sua, não de engenharia

**Marco Civil art. 15 × "nunca gravar IP".** Provedor de aplicação com fins econômicos deve
guardar registros de acesso por 6 meses. Mas `internal/agentreports` declara em comentário
que este servidor **nunca** grava IP nem identificador de rede — e o `accessEntry` do log não
tem campo de IP, por desenho. As duas coisas não coexistem.

O plano entrega a tabela `registros_acesso` **cifrada, com expurgo exato em 6 meses e
desligável por configuração**. Gravar, não gravar, ou sustentar que a rede social não tem
fins econômicos é decisão sua, e vai para ADR com a data.

---

## 13. Superfícies sociais — desenho verificado

### 13.1 Correção a uma afirmação minha

Eu escrevi em §6.4 que `tools/check-sem-caminho-para-metadados` "testa que `/webhook`,
`/api/webhook`, `/proxy`, `/fetch` retornam 404". **Errado.** Ele é **scanner estático de
fonte Go** (`:60-107`): procura endereço de metadados de nuvem e chamadas
`http.Get/Post(r.URL.Query()/r.FormValue…)`. A frase sobre 404 é a *mensagem de OK* dele,
não uma asserção de rede.

**Consequência boa:** `/api/v1/redesocial/*` **não** esbarra nesse gate. O que esbarraria é
buscar URL escolhida pelo cliente — por exemplo, avatar por URL. Por isso **avatar é upload,
nunca URL**, e nenhuma rota de escrita faz requisição de saída com destino do cliente.

### 13.2 A âncora do acervo — medida, e mais cara do que eu supus

**Nenhuma página do acervo tem link para `/redesocial/`** (`grep -rl redesocial public/` →
zero). A "âncora de rodapé já presente" que eu havia imaginado **não existe**; precisa ser
criada, e isso muda as 10.141 rotas.

Três alternativas descartadas com motivo: `sub_filter` do nginx não atua sobre corpo
pré-comprimido e faria o byte servido divergir do `html_sha256` do manifesto; injeção por JS
viola o contrato e a CSP; e a malha de links cobre só **6.282** das 10.141 rotas.

**A solução é um espelho de caminho, sem tabela e sem estado:**
`/familia/alienacao-parental/` ⟷ `/redesocial/tema/familia/alienacao-parental/`.
Caminho inteiro, não slug achatado, porque **108 slugs colidem entre áreas** (medido) — um
slug achatado exigiria desambiguação, logo tabela, logo estado, e estado quebra a premissa
de "escrito uma vez, nunca mais mudado".

Uma linha no emissor de rodapé (`render.go:273` e `:885`), com `href` derivado de
`page.Path`: ~110 B × 10.141 ≈ **1,1 MB**, 0,55% do acervo. Deploy **único** com
`--ressemear` (que regrava a linha de base sem carimbar data nova), purga ampla conferindo
antes o `edge_cache_purge.jsonl`, e na mesma janela a segunda linha `Sitemap:` no
`robots.txt`. **Depois disso, `public/` nunca mais é tocado.**

E a âncora entra em **F2**, não em F1: publicar 10.141 links para uma rota que ainda não
responde seria mandar o Googlebot a uma superfície morta.

**Tema sem thread nasce `noindex,follow`** e entra no índice na primeira dúvida publicada —
anunciar 10.141 páginas vazias é conteúdo fino em massa. `check-social-indexavel` afirma as
duas direções.

### 13.3 O gate de ética obriga um campo no formulário

`oabgate.checkVeracity` é **HARD** e dispara sempre que o corpo casa `art. N`, `lei N`,
`súmula N`, `tema N`, `decreto N` **sem** `SourceProvenance` com `SourceURL` **e**
`CheckedAt`. Comentário jurídico sem citar norma é raro — logo, **sem campo de fonte no
formulário, o gate bloquearia quase toda resposta de advogado**.

Então o formulário de resposta tem, obrigatoriamente, pares `fonte_nome` + `fonte_url`, e o
`CheckedAt` é carimbo do servidor. Isso não é atrito inventado: é o que torna a resposta
citável por agente de IA e o que sustenta o E-E-A-T da thread.

**E o gate não é o mesmo para leigo:** rodar as 14 regras do Provimento 205 sobre a dúvida de
um leigo produziria falso positivo em massa ("meu caso é urgente", "quanto custa"). O leigo
**não é anunciante**. `AvaliarDuvida` roda só `pii` + `publicidadenome`; `AvaliarComentario`
roda o `oabgate` completo.

### 13.4 Feed: duas bandas, chave determinística

**`(banda, data)`**, com `banda ∈ {aguardando, respondidas}`. Aguardando: sem resposta de
verificado, últimos 30 dias, **mais antiga primeiro**, até 10 itens. Respondidas: o resto,
mais recente primeiro, até 20 no total.

Não é score: não tem peso, decaimento nem sinal de engajamento. Quatro razões, e a primeira
é de produto: **ordenação por recência pura starva quem postou às 3 h** — às 9 h a pergunta
já saiu da tela. "Mais antiga sem resposta primeiro" põe cada pergunta no topo exatamente
quando o risco de abandono é máximo, e transforma a métrica "resposta em menos de 24 h"
(§7.9) em **consequência mecânica da ordenação**, não em esperança. Também é cacheável na
borda (anônimo e bot recebem os mesmos bytes) e é auditável por uma consulta SQL.

Personalização muda **filtro**, nunca ordem: `/redesocial/area/{area}/` e
`/redesocial/seguindo/` (privada). **Zero fan-out** — `seguindo` é um `JOIN` indexado.

### 13.5 Seguir assimétrico, e o alvo polimórfico resolve o arranque

Amizade simétrica publicada entre um advogado e centenas de leigos é, funcionalmente, a
**lista de clientes** que o CED art. 42, IV veda. Por isso: seguir assimétrico, e nem
seguidores nem seguidos são públicos — só a contagem, que não entra em ordenação nenhuma.

**O alvo é polimórfico** (`conta | tema | area | duvida`), e é essa a peça que resolve o
arranque: no dia 1 não há gente que valha a pena seguir, **mas há 10.141 temas**. Seguir tema
é o que dá conteúdo ao feed de quem ainda não conhece ninguém.

### 13.6 Orçamento de bytes — a única tela apertada

| Rota | Total | Folga sobre 50 KB |
|---|---|---|
| Feed | 12.870 B | 74% |
| Tema | 15.260 B | 70% |
| **Thread com 12 respostas** | **47.620 B** | **7%** |
| Perfil | 12.470 B | 75% |
| Post de blog | 32.520 B | 35% |

A aritmética que fixa o teto: `51.200 − 2.820 (casco) − 1.800 (JSON-LD) − 2.300 (pergunta) −
1.700 (form) = 42.580 B` para respostas; a 3.250 B por resposta, **N = 12** por página, com
3.580 B de margem. Respostas 13+ vão para `/pagina/2/`, com `rel=next/prev` e self-canonical
— **nenhuma resposta sai do índice**.

Duas decisões que compram folga: **paginação por caminho, nunca feed infinito** (infinito
exige JS e é invisível ao crawler) e **sem avatar em lista** — a "foto" é um `<span>` com as
iniciais e `aria-hidden`, o que economiza ~1,4 KB por tela, elimina uma classe inteira de
achados de acessibilidade e dispensa `img-src` extra na CSP.

### 13.7 Acessibilidade: a regra que quebraria o feed

`form` **com** nome acessível vira landmark; `form` **sem** nome, não
(`accessibilityaudit/rules.go:194-198`). Vinte formulários de "seguir"/"também tenho" com
`aria-label` produziriam **20 landmarks idênticos** e um achado `SevImportant`.

→ Regra de casa: **formulário de ação em lista não leva `aria-label`** — o nome vai no
`<button>`, que não é landmark. Só o formulário principal da tela leva nome. Do mesmo modo:
card é `<article>` (não é landmark), nunca `<section aria-label>` (que vira `region`);
`id` gerado em lista leva o id da entidade (`r-8412-corpo`) contra `ruleDuplicateIDs`; e
nenhum `<aside>` dentro de `<main>`.

Como `htmlcontract` não roda por requisição, a verificação vive num **teste de pacote** que
renderiza um fixture de cada rota e falha em qualquer achado `SevImportant`.

### 13.8 Duas travas que eu não tinha visto

**O cookie precisa se chamar exatamente `wjsession`.** O `location` do nginx chaveia em
`$cookie_wjsession` para `proxy_cache_bypass`/`proxy_no_cache`. Nome diferente = bypass que
nunca dispara = vazamento de sessão pelo cache. `check-social-cache` prova os dois lados.

**A licença da gêmea social é `CC-BY-NC-ND-4.0`, não `CC-BY-4.0`.** O acervo declara CC BY
4.0 em todo JSON-LD e em toda gêmea; mas o texto da rede social é de **terceiro**, e o portal
não tem cessão para relicenciar. Declarar CC-BY ali seria licenciar o que não é nosso.

**Consequência em F5:** promover um post de terceiro ao acervo exige **consentimento
explícito e datado do autor** para relicenciar em CC BY 4.0. É o sétimo critério da promoção,
e é o que ninguém lembra. Sem o aceite, o acervo no máximo **cita** a thread.

E fica registrado um ponto que precisa de ADR antes de F5:
`structureddata.authorMatchesConfiguredIdentity` só atribui `Article.author` quando o autor
coincide com a identidade única de `content/site.json` — **a maquinaria de autoria do acervo
é mono-autor por construção**. Página nascida de post de terceiro não cabe nela hoje.

---

## 14. Cobrança sem terceiro no caminho crítico

Fonte primária: **Manual de Padrões para Iniciação do Pix, v2.10.0** (BCB), baixado e lido.

### 14.1 Onde exatamente a linha corta

| O que | Precisa de PSP? | Fonte |
|---|---|---|
| **QR Pix estático (BR Code)** | **NÃO** — 100% offline | Manual, p.14: *"O QR Code estático pode ser criado diretamente pela automação do usuário recebedor… A criação do QR Code estático **NÃO** é uma funcionalidade que faz parte da API Pix"* |
| Confirmação automática do pagamento | **sim** | consulta de Pix por `txid` passa pela API Pix |
| QR dinâmico, webhook, cobrança `cob` | **sim** | Anexo II, p.65-67: OAuth2 client_credentials + **mTLS obrigatório**, onboarding em ambiente logado no PSP |
| **Pix Automático** (recorrência *pull*) | **sim**, e o PSP **recebedor** tem de oferecer | Res. BCB 402/2024; público desde 16/06/2025; obrigatório só do lado do pagador |
| Boleto | sem *gateway* sim, **sem banco não** | Nova Plataforma de Cobrança (CIP/FEBRABAN): nenhum boleto circula sem registro prévio em banco |
| Virar participante direto do Pix | **é virar banco** | capital mínimo ~R$ 5 mi + autorização do BACEN (Res. BCB 80/2021) |

O QR estático é TLV do padrão EMV-QRCPS, com **CRC-16/CCITT-FALSE** (polinômio `0x1021`,
inicial `0xFFFF`) — que não está na stdlib do Go (`crc32` e `crc64` existem, `crc16` não),
mas são ~20 linhas. O encoder inteiro é **150–200 linhas**: construir em casa, sem
dependência e sem ADR para algo trivial.

### 14.2 As três fases

**Fase 0 — hoje, zero credencial nova.** Um QR Pix estático **por assinante**, com o `txid`
(até 25 caracteres) carregando o identificador interno da cobrança, gerado em Go a partir da
chave Pix que o dono já usa. Conciliação lendo o extrato OFX/CSV da conta PJ pelo
*internet banking* que já existe — não é credencial nova, é a mesma conta. Nota fiscal
manual, pelo portal do Emissor Nacional.

**Fase 1 — quando o volume justificar.** Uma credencial de API Pix, atrás de interface
própria e removível sem tocar o núcleo. Troca conciliação manual por webhook. Ainda não é
recorrência automática: o assinante paga todo mês, só a confirmação vira automática.

**Fase 2 — Pix Automático**, quando o PSP recebedor suportar. Aí sim, cobrança mensal sem
ação do pagador.

**Ficam fora, com razão:** boleto (mesma barreira de PSP, custo maior, nenhuma vantagem
sobre Pix para este público); Open Finance para ler extrato (exige agregador pago ou virar
participante — sem rota própria gratuita).

### 14.3 Bibliotecas

| Necessidade | Decisão | Motivo |
|---|---|---|
| Payload BR Code + CRC16 | **construir** | 150-200 linhas sobre spec pública |
| Renderizar QR | `yeqown/go-qrcode/v2` — **MIT, v2.3.0 de 05/08/2026**, ativo | Reed-Solomon não é trivial; é o único item onde a lib poupa trabalho real. Entra com o ADR padrão |
| Parser OFX | **construir** | `aclindsa/ofxgo` é **GPL-2.0** (não permissiva) e está parado desde 2021. OFX é SGML simples |
| CNAB | `gocnab` (MIT) **se** entrar em cena | não entra na fase 0; conferir maturidade por `git log` real antes de adotar |

### 14.4 O achado que decide a estrutura: quem emite a nota

**Lei 8.906/94, art. 16, §3º** veda à sociedade de advogados ter **"atividade estranha à
advocacia"** como objeto social. Logo **nem a sociedade de advocacia nem a pessoa física do
advogado** é o veículo fiscal certo para faturar SaaS ou curso.

A rota limpa é uma **segunda pessoa jurídica comercial**, com objeto de tecnologia e
educação, separada da sociedade. E isso tem um efeito colateral excelente: **satisfaz
mecanicamente o CED art. 40, IV** (vedada divulgação conjunta de advocacia com outra
atividade) — é um CNPJ diferente, emitindo nota diferente, num checkout diferente. A
separação que a norma de ética pede vira consequência da estrutura societária, não uma
disciplina de UI.

É decisão de constituição societária, e portanto sua.

**NFS-e programática exige certificado A1** (arquivo `.pfx` que fica carregado no processo),
não o **A3** do dono — que vive em token físico, na VM do PJe/e-SAJ, território que o próprio
contrato do projeto veda automatizar. É credencial nova de fato, mas de natureza **fiscal
obrigatória por lei**, categoricamente diferente de uma API key de SaaS evitável.

### 14.5 A régua da OAB sobre dinheiro, com honestidade sobre o que não existe

Busca específica por manifestação da OAB (TED, parecer, nota técnica) sobre **software
jurídico por assinatura**: **não há decisão nomeada**. Nem a favor, nem contra.

Então a leitura correta: cobrar assinatura de software do advogado **não esbarra em nenhum
dispositivo nomeado**. Mas o risco não some por trocar o rótulo — **um TED julga substância,
não nome**. Se a "assinatura" comprar posição na busca, prioridade de indicação ou volume de
conexão de caso, ela é `destaque_pago` disfarçado (Prov. 205 art. 5º), diga o contrato o que
disser. Se o produto for genuinamente ferramenta — painel de prazos do DJEN, organização,
acompanhamento (§7.9, item 3) — o enquadramento como comércio comum se sustenta.

Aqui não há corte desenhando o limite: **é você quem desenha**. E é por isso que a trilha
datada de `internal/socialpolicy` (§10.1) vale mais do que qualquer parecer — ela registra o
que o sistema fazia e quando.

### 14.6 A lacuna que só se fecha olhando

O item que mais importa para a Fase 0 funcionar **não se resolve por pesquisa**: é saber se
o extrato do banco que o dono usa **expõe o campo `txid`**. O `EndToEndId` sempre existe e
serve para deduplicar, mas é gerado pelo PSP do pagador e não correlaciona com uma cobrança
específica. Sem `txid` no extrato, a conciliação automática da Fase 0 cai para casamento por
valor e data — que funciona com poucos assinantes e degrada rápido. **Verificar num extrato
real antes de escrever o conciliador.**

---

## 15. Segurança, LGPD e moderação — desenho verificado

Última frente. As três lacunas de borda que ela achou já subiram para §7.1-bis(4)(5)(6), por
serem P0 de roteamento. O que segue é o resto, e há duas medições que **refutam** desenhos
meus (§12.2 já corrigida: Argon2id e o nome do cookie).

### 15.1 As filas do STF são trava de banco, não política

Princípio, copiado literalmente do `agentreports`: *"se relatar pudesse mudar estado de
serviço, relatar viraria arma de censura"*. Numa rede social vale mais, porque o regime
pós-STF **cria incentivo a remover**. **Denúncia nunca remove. Denúncia abre fila com humano
do outro lado.**

A peça central é que a **tese 2 vira `CHECK` constraint**, não regra de código:

```sql
CHECK (tipo_fila <> 'honra' OR resultado <> 'remover' OR ordem_id IS NOT NULL)
```

Nenhum caminho de código, nenhum modo de emergência e nenhum operador remove conteúdo de
honra sem ordem judicial — é violação de constraint. `tipo_fila` fica **desnormalizado de
propósito** em `decisoes`, porque `CHECK` do SQLite **não aceita subquery**; uma FK composta
para `fila_moderacao(fila_id, tipo_fila)` garante que o valor não mente. A mesma técnica
sustenta duas outras invariantes: recurso nunca é julgado por quem decidiu
(`revisor_id <> revisor_original_id`), e **só ordem judicial gera bloqueio automático de
repostagem por hash** — deixar notificação extrajudicial fazer isso transformaria uma
notificação falsa numa chave de censura permanente.

A trilha é append-only por `TRIGGER … RAISE(ABORT)`, encadeada por
`sha256(encadeamento_anterior || linha)`, e carrega a **versão da `socialpolicy` vigente
naquele momento** — que é o que torna a trilha datada de §10.1 prova, e não alegação.

**A recepção de denúncia é cópia estrutural do `agentreports`**, e cada elemento tem função:
enum fechado de categoria; tetos de campo; **âncora anti-invenção** (o trecho citado tem de
ocorrer no conteúdo denunciado — denunciar passa a exigir ter lido, barato de boa-fé e caro
em campanha); `denuncia_id` determinístico, de modo que campanha coordenada **colapse na
mesma linha** com `repeticoes`, virando sinal em vez de 300 filas; cota **por conta** (o Go
não vê IP, §7.1-bis(5)); e resposta **202 `recebida_para_triagem`** — não "aceita".

**Prazos são parâmetro de produto declarado, porque as teses não fixam número:** 24 h para
nudez não consentida e conteúdo infantil; 72 h para crime/ato ilícito e conta inautêntica;
**72 h para *responder* na fila de honra** (a resposta padrão explica o que a ordem judicial
precisa conter, Marco Civil art. 19 §1º); 7 dias para ética OAB; 15 dias para recorrer e 15
para julgar. Fila que estoura prazo **falha fechada** — "atrasada", nunca "sem item =
saudável", invariante copiado de `coleta.go:133-141`.

**O dever de cuidado ativo (tese 4) produz sinal, nunca remoção.** `Analisar(texto) []Sinal`
compõe o que já existe e está testado: `publicidadenome.PodeVirarCorpoDePagina` (as 4
categorias com `vedacaoLegal: true` — e **aqui o padrão se inverte em relação ao acervo**:
lá elas governam republicação de ato público; em UGC, post que nomeia vítima de crime sexual
ou revela ato infracional é exatamente o que a tese manda prevenir), `pii.Mascarar` (CPF/RG
mascarados **antes** de publicar; nome civil continua não mascarado, §2.1) e o `oabgate`.
Filtro que remove sozinho é filtro cujos falsos positivos ninguém vê — e este repositório já
mediu o custo disso nas 88 ocorrências de "[nome removido]".

**Correção a uma afirmação minha na §6.1:** eu escrevi que o `oabgate` "só precisa ser
ligado". Ele recebe **`content.Page`**, não string (`oabgate.go:50`). A mudança limpa é
**exportar `oabgate.CheckCampos(map[string]string) []Issue`** e fazer `CheckPage` chamá-la —
aditivo, preserva as 501 linhas de teste, e evita fabricar uma `content.Page` falsa.

**Limite honesto, que fecha uma porta de produto:** **não existe capacidade self-hosted de
casamento de hash de material de abuso infantil**, e não se constrói uma sem acesso a uma
lista que não é pública. A mitigação é arquitetural: **nenhum upload de imagem em F1–F2 além
do avatar**, e o avatar é re-encodado no servidor (decodifica → re-encoda → descarta todo
metadado → dimensão fixa), o que destrói EXIF e esteganografia. Postagem pública de imagem é
decisão separada que **exige uma capacidade de moderação que hoje não existe**.

**Relatório anual de transparência** em `/redesocial/transparencia/` + gêmea Markdown +
`transparencia.json`, acumulado diário **agregado e sem PII** em
`data/ops/moderacao_transparencia_diaria.jsonl`. Publica, entre outros, **itens sinalizados
pelo filtro × quantos viraram remoção — ou seja, a taxa de falso positivo do próprio
filtro**, que é o número que o mantém honesto e que quase nenhuma plataforma publica. E
publica as três coisas que o STF exige e que **hoje não existem em lugar nenhum do portal**:
encarregado (LGPD art. 41), canal de atendimento e representante legal no Brasil.

### 15.2 LGPD: base legal por finalidade, e o conflito real resolvido

Tabela `finalidades` versionada no banco, com base legal, retenção, marco de contagem e se é
eliminável pelo titular. As nove linhas da semente vão da conta (art. 7º, V) ao intake de
caso (art. 7º, V e VI + art. 11, II, "d" para sensível), passando por moderação (art. 7º, II
— as teses do STF **impõem** a trilha, então ela **não** é eliminável, art. 16, I) e por
`seguranca` (**Marco Civil art. 15, 6 meses**, que é o item que mata a fantasia do "apago
tudo", já que a plataforma vai cobrar em F6).

**O conflito real é art. 18 × conteúdo público já publicado**: alguém publica uma dúvida,
advogados respondem, a thread vira página indexada, e depois o titular pede eliminação. A
resolução **é escolha do titular**, apresentada com três opções:

- **(a) Anonimizar a autoria — o padrão oferecido.** O texto fica; o vínculo pessoa↔texto
  sai. Fundamento: o texto é a contribuição ao debate público, o dado pessoal é o vínculo, e
  o art. 12 põe dado anonimizado fora do escopo da lei. Toda resposta de terceiro continua
  fazendo sentido, que é o que uma remoção quebraria.
- **(b) Remover o próprio conteúdo.** Rota devolve **410 Gone**, sai do sitemap, gêmea
  Markdown some, borda purgada por alvo. **Resposta de terceiro sobrevive**, com o pai
  exibido como "mensagem removida pelo autor" — **ninguém apaga a fala de outra pessoa**, e
  isso vai escrito nos termos.
- **(c) Eliminação da conta**: (a) + (b) + apagamento, menos o resíduo legal
  (moderação, 6 meses de registro de acesso, fiscal, ordem judicial cumprida) — que fica
  **pseudonimizado**: sobra id opaco, e-mail e nome saem.

**O aviso tem de dizer o que a plataforma NÃO consegue fazer:** conteúdo público foi
indexado e lido por agente de IA **de propósito** (§7.3), e isso é irreversível em cache de
terceiro. Prometer mais é a classe de mentira que este contrato proíbe.

**Por que isso não colide com "nunca reverter trabalho" (R10):** a regra é sobre artefato
versionado no git. O dado do titular vive **só no SQLite, fora do versionamento** (§7.4) —
concretamente, **uma eliminação jamais toca `data/`, `content/`, `v2_pages/` ou `public/`**.
O único ponto de encosto é a ponte editorial de F5, e a trava é de desenho: **thread só vira
candidata a página v2 depois de a autoria ser desvinculada e o texto reescrito
editorialmente; a página v2 nunca carrega `conta_id`**. Gate
`check-ponte-editorial-sem-autoria`.

**Portabilidade** (art. 18, V): `GET /api/v1/redesocial/contas/eu/exportar`, com
`schema_version` e `manifest.json` com sha256 por parte — mesma disciplina de artefato do
repositório. Uma por conta a cada 7 dias, por **URL assinada de uso único válida por 24 h**,
nunca por anexo de e-mail. Inclui as conversas de que o titular é parte; **não** inclui
e-mail nem telefone da contraparte.

**Duas travas de SQLite que não podem faltar:** `PRAGMA foreign_keys = ON` é **por conexão**
(o SQLite nasce com FK desligada e o `database/sql` usa pool — e o padrão da casa,
`storageindex/index.go:509`, executa pragma como *statement*, o que funciona para
`journal_mode` porque ele é persistido no arquivo, mas **não funcionaria para
`foreign_keys`**); e `PRAGMA secure_delete = ON`, sem o qual linha apagada sobrevive nas
free pages e o art. 18, VI vira ficção.

### 15.3 O gap do aviso de privacidade, e o gate que o fecha

`/privacidade/` **no ar hoje** promete tratar "documentos pessoais e documentos ligados ao
caso" sob a LGPD, com sigilo e retenção. **Nenhum código faz isso** — a única escrita HTTP é
o `agentreports`, cujo comentário diz que **nunca grava IP**, e o `contactchannel` resolve um
link `wa.me`. O documento nunca toca o servidor.

O que precisa existir para a promessa virar verdade: recepção autenticada com allowlist de
content-type, `MaxBytesReader` e **nome de arquivo nunca ecoado**; cifra em repouso
(§15.5); `casos_participantes` com toda leitura passando por função que recebe a conta
requerente; varredor de retenção por timer; e **trilha de acesso que o próprio cliente vê**
("quem abriu o meu documento e quando") — é essa prestação de contas que torna o
compartimento crível.

**Gate `check-promessa-privacidade-tem-substrato`:** lê as afirmações estruturadas do aviso e
reprova se alguma finalidade declarada não tiver linha em `finalidades` com código que a
implemente. É o gate que impede o aviso de voltar a prometer o que não existe.

**Ordem inegociável, pela mesma lógica que o `oauthserver` já documenta:** o aviso só é
reescrito **depois** de o código existir. Reescrever antes repete exatamente o defeito.

Reescritas obrigatórias em `/privacidade/`: **separar o papel de controlador** (a plataforma
é controladora de conta, conteúdo público, moderação e segurança; o advogado é controlador
do caso — separação que protege o sigilo do cliente das obrigações da plataforma); seção
nova **"o que acontece com o que você publica"**; e a garantia — **por código, não por
intenção** — de que nenhum UGC, mensagem ou documento passa por GA4/Clarity. O mecanismo de
hoje é uma checagem de path dentro do loader (`webanalytics.go:289`), frágil demais aqui: o
**`cmd/social` simplesmente não emite o loader em rota autenticada**, e a CSP da variante
privada nem lista os hosts de analytics. Gravação de sessão numa tela com conversa
cliente-advogado é violação de sigilo, não configuração de analytics.

Em `/termos/`: licença do usuário para exibir, indexar, gerar a gêmea Markdown e **servir via
MCP/A2A** — explícita, porque é incomum e é exatamente o que §7.3 faz; moderação e recurso;
onde enviar ordem judicial e o que ela precisa conter; o que o selo de OAB significa; e **a
régua do art. 42, I como regra de uso** (§1.3), que é a restrição jurídica central do produto
e sobre a qual os termos de hoje não dizem nada.

### 15.4 Anti-abuso sem CAPTCHA de terceiro

A restrição que decide tudo: **§7.2 exige que a página funcione sem JavaScript.** Logo
**prova de trabalho só pode LEVANTAR limite, nunca ser portão** — um portão de PoW é falha de
acessibilidade e de visibilidade para bot ao mesmo tempo.

1. **Borda** — as zonas próprias de §7.1-bis(6).
2. **Quarentena de conta nova**: 7 dias **e** 3 posts sobrevividos. 5 posts/dia, 20
   comentários/dia, **nenhum link externo** (a superfície de spam mais valiosa), sem DM a
   quem não segue de volta. Os 3 primeiros posts são **publicados** e marcados
   `revisao_leve` — escondê-los quebraria §7.3 e esconderia o abuso justamente de quem melhor
   o denunciaria.
3. **Rate limit por conta no Go** (`x/time/rate`, já no `go.mod`) **mais contador diário
   persistido**: o `agentreports` pode zerar no restart porque cliente é efêmero; conta é
   longeva e o orçamento tem de sobreviver.
4. **Reputação** como regulador interno, **nunca exibida como ranking** — placar público
   esbarra no Prov. 205 art. 5º e na linha `ordenacao_por_conversao` de §10.1. Destrava link
   externo (≥5), DM a desconhecido (≥10), abrir thread (≥20).

   > **Nota de 2026-09-24.** Esta cláusula continua em vigor e tem objeto certo: a reputação
   > **por conta humana** desta rede (`content/social_policy.json` → `.reputacao`,
   > `exibida_publicamente: false`, cobrada por `internal/socialpolicy/policy.go:749-756` e pelo
   > gate `social-policy`), porque o Prov. 205 art. 5º mira ranking de advogado. Reputação de
   > **agente de IA** é outro objeto: `REDE_SOCIAL_DE_IA_RASCUNHO.md:573-578` deixou a de
   > `client_id` em aberto, e o CANON v4.1 (§0 e §12) a fecha — `rep_wjr` e MeritRank públicos
   > para as quatro personas do EnaEval (chaves da PJ, nunca da PF) e para agentes externos; a F6
   > da TASKLIST executa como escrita. Nos dois regimes continuam fora ranking de vara ou juiz e
   > `judge_id` (Res. CNJ 615/2025). Ver `docs/goal/enaeval/PONTE_CEREBRO_E_REDE_SOCIAL.md` §5 e
   > DEC-062.

5. **PoW como aceleradora**: resolver **eleva** o orçamento por minuto da sessão e dispensa o
   atraso do primeiro post; não resolver **não bloqueia nada**. 18 bits (~0,3 s num celular),
   subindo no modo "sob ataque". Satisfaz "sem terceiro" e "funciona sem JS" ao mesmo tempo —
   o que nenhum CAPTCHA faz.
6. **Sem JS, o que barra robô**: tempo mínimo até o envio (timestamp com HMAC, recusa abaixo
   de 2 s **com erro legível**, nunca descarte silencioso), campo de armadilha que manda para
   fila em vez de descartar, e a exigência de e-mail verificado — que é o verdadeiro centro
   de custo da conta falsa.
7. **Credential stuffing sem bloqueio duro de conta** — bloquear por senha errada entrega ao
   atacante uma negação de serviço contra qualquer usuário cujo e-mail ele conheça. Backoff
   exponencial por conta a partir da 4ª falha, e **modo "sob ataque"** por janela de 5 min
   que exige OTP por e-mail para todas as contas até baixar: é o mecanismo que sobrevive a um
   ataque distribuído em que o limite por IP e o por conta parecem ambos normais.
8. **Recuperação e cadastro sem virar oráculo de enumeração.** Sempre o mesmo 202 e a mesma
   latência — e para igualar a latência, o ramo "não existe" roda **um Argon2id dummy contra
   constante**, que é exatamente a manobra de `oauthserver.go:316-318` (`ConstantTimeCompare`
   contra 64 zeros, *"para o tempo de resposta não revelar se o cliente existe"*). Cadastro
   com e-mail já registrado devolve o mesmo 202 e manda ao endereço existente uma mensagem
   **diferente**.
9. **Conta inautêntica (tese 3)**: sinais calculados de madrugada e **nunca acionados
   automaticamente** — agrupamento de cadastro por /24, `ua_hash` idêntico, variância de
   intervalo de postagem, **mesmo texto normalizado por ≥3 contas** (reusa a maquinaria de
   dedupe que já existe), densidade anômala no grafo de follows. Saída: **uma linha de fila
   por cluster**, com evidência, para um humano. A presunção do STF é relativa e elidível por
   remoção diligente — o que a torna elidível é o registro datado de ter olhado.
10. **`contas.papel` não tem rota que o escreva a partir de entrada do usuário.** O único
    escritor é a decisão de verificação, e o selo é renderizado **por join** com
    `resultado='deferida' AND vigente_ate > now()` — nunca de coluna do perfil, nunca de
    booleano em cache. `vigente_ate` de 12 meses; a evidência (foto da carteira) é apagada 30
    dias após a decisão e sobra só o `sha256`, para a trilha provar que algo foi revisado sem
    guardar documento de identidade para sempre. Ninguém verifica a si mesmo — `CHECK` de
    banco. A ação do revisor exige sessão com menos de 15 min **e** re-digitação da senha.
11. **SSE limitado a 2 conexões por conta e 10 por IP**, com heartbeat e vida máxima de 30
    min — endpoint SSE sem teto é a forma mais fácil de esgotar descritor nesta máquina.

### 15.5 O compartimento de sigilo, e o ataque que mais preocupa

**O requisito, sem rodeio: o operador — o dono — não pode conseguir ler conversa alheia por
acidente.** O EOAB art. 34, VII faz da violação do sigilo **infração disciplinar**: não é "um
incidente", é a inscrição OAB/RJ 227191 em risco.

E o ambiente empurra para o acidente: 46 timers rodando como o dono; sessões de agente com
acesso ao disco; `.env.local.bak-20260819` na raiz do repositório; `data/` versionado; e uma
cultura de "meça tudo e escreva um ledger JSONL" que vai, **por inércia e boa intenção**,
produzir um `tools/measure-social-engajamento` que faz `SELECT texto FROM mensagens` e
escreve um resumo em `data/ops/`. Ninguém age de má-fé em nenhum passo dessa cadeia.

→ **Conclusão de desenho: a chave não pode morar no ambiente.** Isso **substitui** a
`WIKI_SOCIAL_KEK` que a §12.5 propunha para o conteúdo de caso — KEK em variável de ambiente
é lida por todo agente, todo timer e todo backup. (A cifra por campo de §12.5 continua válida
para e-mail, evidência de verificação e registro de acesso, que a plataforma **precisa** ler
para operar; o compartimento de caso é regime diferente.)

- **Par X25519 por conta** (`x/crypto/curve25519`, verificado presente em v0.55.0). Privada
  guardada **envelopada** por chave derivada da **senha**, com `sal_chave` **diferente** do
  `sal_senha` — senão a coluna de hash de login seria a chave.
- **Chave por caso**, 32 bytes, envelopada uma vez para a pública de cada participante
  (`x/crypto/nacl/box`). Entrar = envelope novo; sair = rotação para mensagens futuras, com
  as passadas ainda legíveis a quem saiu — é a verdade do que aconteceu e é o que o dever de
  guarda exige.
- **Conteúdo em XChaCha20-Poly1305**, nonce aleatório de 24 bytes, **AAD =
  `caso_id || documento_id || schema_version`** para que um ciphertext não possa ser movido
  entre casos. XChaCha e não AES-GCM porque nonce aleatório de 24 bytes não tem problema de
  aniversário — este código vai rodar anos sem contador de nonce para alguém errar.
- **O trade-off vai declarado no aviso e nos termos, não escondido: isto NÃO é criptografia
  ponta-a-ponta.** O desenvelopamento acontece no servidor, em memória, na requisição que tem
  a senha. Ponta-a-ponta exigiria a chave nunca chegar ao servidor, o que exige JavaScript
  obrigatório, o que §7.2 proíbe. O que este desenho defende é exatamente a ameaça que
  importa aqui — **o operador, uma sessão de agente, um disco roubado, um backup vazado** —
  porque nenhum deles tem a senha. Não defende contra servidor comprometido em execução.
- **Não há chave de administrador, de suporte, nem "quebra-vidro".** Ordem judicial de
  exibição é cumprida pelo **advogado** produzindo a cópia dele — que é, aliás, a postura
  juridicamente correta, porque o sigilo é do cliente e é oponível pelo advogado.
- **Mensagem privada está FORA da moderação de conteúdo.** O dever de cuidado do STF mira
  conteúdo **público**; plataforma que varre conversa advogado-cliente comete a violação que
  diz prevenir. Um participante ainda pode denunciar, decifrando na própria sessão e
  **citando** o trecho — o ato de denunciar é o que torna aquele trecho visível ao revisor, e
  a trilha registra que o denunciante era parte. É o único caminho, e é o correto.
- **Notificação nunca carrega conteúdo** — "você tem mensagem nova", link, nada mais. É a
  restrição de segurança sobre o canal desacoplado de §3.

**Três gates tornam a propriedade verificável em CI, em vez de confiada à disciplina:**
`check-sigilo-sem-texto-claro` (reprova se conteúdo de sigilo decodificar como UTF-8 com
perfil de frequência do português), `check-sem-dado-pessoal-em-git` (reprova se o banco
social, qualquer `.enc` ou JSONL com `@`/padrão de CPF aparecer em `git ls-files`) e
`check-social-sem-chave-no-ambiente` — que afirma a **ausência** do desenho que quebraria a
propriedade.

**O ataque mais provável e de pior consequência é esse mesmo: o vazamento do compartimento
pela ferramenta do próprio operador.** Não é o mais sofisticado. É a única falha aqui que é
infração disciplinar **contra o dono pessoalmente**, o ambiente empurra para ela, e ela falha
em silêncio e é permanente — descoberta pelo cliente, ou pela parte contrária, num processo.
Com a chave derivada da senha do participante, o pior que um ledger desgovernado produz é uma
contagem de blobs cifrados.

**Vice-campeão, e é o que vai acontecer primeiro: denúncia coordenada como arma de censura
contra advogado.** Uma parte adversa insatisfeita despeja denúncias em `crime_contra_honra`
contra o comentário técnico legítimo de um advogado. A mitigação é inteira no desenho de
§15.1: a plataforma **não consegue** remover sem ordem judicial nem que queira; a denúncia
tem cota e âncora; denúncia infundada repetida custa reputação; e o relatório publica a razão
entre denúncias e decisões procedentes por categoria, o que torna a campanha visível em
número público.

### 15.6 CSP em duas variantes, e o CORS que vaza

Anônimo (cacheável, com analytics, indexável) e autenticado (nunca cacheado, sem analytics,
`noindex`) têm requisitos opostos — e `more_set_headers` é **tudo-ou-nada por nível**, como o
próprio `security-headers.conf` documenta. Logo, **duas listas completas**:
`social-headers-publico.conf` e `social-headers-privado.conf`, esta última sem nenhum host de
terceiro e com `Cache-Control: private, no-store`, `X-Robots-Tag: noindex, nofollow,
noarchive` e `Referrer-Policy: same-origin`.

O que muda em relação ao acervo, e por quê: `style-src` com a URL exata da folha social e
**zero hash inline** (UGC + estilo inline é o caminho de injeção; a superfície nova nasce sem
inline); `frame-src`/`worker-src`/`manifest-src`/`media-src` **declarados `'none'`
explicitamente** em vez de cobertos por `default-src`, para que uma diretiva futura não abra
um sink calado; **`require-trusted-types-for 'script'`**, que fecha DOM-XSS vindo de conteúdo
de terceiro e custa quase nada numa superfície sem framework; `report-uri
/api/v1/redesocial/csp-report`, porque com UGC a violação de CSP é o primeiro sinal de
injeção (endpoint rate-limitado, grava só agregado, **nunca ecoa o `blocked-uri` bruto numa
página**); e CORP `same-origin` **fixo**, não pelo `map $request_uri` do acervo, para que uma
rota social não vire `cross-origin` por acidente.

**Achado medido que é P0 e eu não tinha visto: `Access-Control-Allow-Origin: *` aparece em 9
pontos do `cmd/server`** — `a2a.go:587`, `apimd.go:409`, `api_lote.go:315`,
`agentskills.go:240` e `:290`, `descritores.go:536`, `authmd.go:427`,
`artefatosestaticos.go:93`. É correto lá (canal de máquina público, sem cookie). **Na rede
social é a combinação que vaza**: rota com cookie de sessão **mais** ACAO permissivo. Gate
`check-social-sem-cors` reprova se qualquer resposta do **8091** trouxer o header.

Mais: `Clear-Site-Data: "cache", "cookies", "storage"` no logout, e `Permissions-Policy`
igual à do acervo — que hoje nega `payment=()` e vai precisar de revisão em F6.

**E a CSP é defesa em profundidade, não a defesa.** A defesa é escape do lado do servidor em
todo campo de UGC (`html/template`, §12.7). **Nenhum campo de UGC aceita HTML bruto**; se
houver Markdown de usuário, passa por subconjunto allowlist e **nunca** por passthrough de
HTML.

### 15.7 Correções que apliquei a este relatório

| O agente escreveu | Corrigido para | Por quê |
|---|---|---|
| `proxy_pass` para **8090** nos blocos de `location`, e `check-social-sem-cors` sondando 8090 | **8091** | §10.3 C4 — 8090 é a porta de ensaio do cutover |
| `KEK` de conteúdo de caso em `WIKI_SOCIAL_KEK` (herdado da minha §12.5) | chave derivada da **senha do participante**, nunca no ambiente | §15.5 — é a própria tese dele, e ela invalida a minha proposta anterior para o compartimento de caso |
| Argon2id `m=19456, t=2, p=1` (minha §12.2) | **`m=65536, t=3, p=2`** + semáforo 4 + `MemoryMax=768M` | hardware medido: i7-8565U ULV com load 1,9 antes da rede social existir |
| Cookie `__Host-rs_sessao` (minha §12.2) | **`wjsession`** | `$cookie_<nome>` do nginx só aceita `[A-Za-z0-9_]` |

**E três itens que ele mesmo marcou ASSUMIDO, e que entram como tarefa, não como fato:**
conferir o verbatim do **art. 15 do Marco Civil** no Planalto com URL e data antes de
escrevê-lo no aviso (R9); confirmar a forma `_pragma=foreign_keys(1)` no DSN do
`modernc.org/sqlite v1.53.0` (se não houver, `ConnectHook` com statement por conexão); e ler
a **licença da lista Pwned Passwords** na fonte oficial antes de qualquer download. O
benchmark do Argon2id nesta máquina **não foi rodado** — ele é a primeira linha de
`data/ops/argon2_calibration.jsonl`, em F1.

**O `ip_hash` do registro de acesso: eu decido, e a decisão é o IP cifrado.** O agente propôs
`ip_hash` (sha256 com sal) e devolveu a escolha ao dono; o §12.9 já dizia "cifrada". As duas
divergiam, e a divergência se resolve pela norma, não pelo gosto: o **art. 5º, VIII da Lei
12.965/2014** define registro de acesso a aplicação como o conjunto de informações de data e
hora de uso *"a partir de um determinado endereço IP"* — a obrigação do art. 15 é sobre o
**endereço**, e hash não é endereço. Guardar só o hash cumpriria a função de correlação
interna (anti-abuso) e **descumpriria a de guarda**, entregando ao juízo uma coluna que não
responde ao que ele pede. **Padrão: IP cifrado por campo, reversível, 6 meses exatos, expurgo
por timer** — exatamente o que a §12.9 já entrega, e é a única leitura em que as duas
funções coexistem. O `ip_hash` fica **em coluna adicional**, para as correlações que não
precisam decifrar (agrupamento de cadastro, clustering da tese 3), o que reduz o número de
vezes que o texto claro é tocado. *Verbatim do art. 5º, VIII e do art. 15 a conferir no
Planalto com URL e data antes de entrar no aviso (R9) — a leitura acima é de conhecimento
consolidado, não de fonte lida nesta sessão.*

**E o SMTP também é decisão minha, não sua.** O agente terminou em "as duas rotas honestas
são decisão sua"; o contrato desta máquina proíbe devolver opção (a) ou (b) ao dono, e
**self-hosted-first já decide**: **MTA próprio no host, com SPF, DKIM e DMARC publicados no
DNS.** Relay de provedor é serviço de terceiro no caminho crítico e fere §0.1. O ponto duro é
real e vira **gate de F1, não ressalva**: a entregabilidade para Gmail e Outlook é **medida**
(mensagem de teste para caixa em cada um, conferindo entrega e pasta), e F1 não fecha sem
essa medição verde. Se a medição reprovar, o problema é de reputação de IP e de DNS, e se
resolve nessa camada.

Estado medido hoje, que é o tamanho do trabalho: `/usr/sbin/sendmail → /usr/bin/msmtp`,
`msmtpd.service` **disabled**, `postfix@-.service` **masked**, nada escutando em 25/587/465,
`/etc/msmtprc` e `~/.msmtprc` **inexistentes**, `.env.local` sem nenhum nome de chave de
SMTP — e o msmtp é **cliente de relay**, não MTA. Sem resolver isso não há verificação de
e-mail, não há recuperação de senha e não há canal de exercício de direito do titular.
Desenho que protege contra a demora: **fila primeiro** — todo e-mail vira linha em
`email_saida` na mesma transação que cria a conta/token, com recuo exponencial —, de modo que
nada se perca e o usuário nunca veja erro por causa do correio.

**O que continua sendo genuinamente seu, e por isso fica:** a constituição da **segunda
pessoa jurídica** de §14.4, que é ato societário; e a colisão de §12.9 sobre **se** gravar
registro de acesso (a alternativa de sustentar que a rede social não tem fins econômicos é
posição jurídica, não escolha de engenharia).
