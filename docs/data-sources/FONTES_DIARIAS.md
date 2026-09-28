# Fontes públicas para conteúdo jurídico diário — matriz medida

> **Origem:** investigação de 2026-08-20 com 26 agentes em 3 ondas, duas críticas adversariais
> (Fable 5 e Opus 5) e verificação própria no disco e no log cru. **Todo número aqui foi medido**,
> não estimado. Plano completo: `docs/goal/PLANO_FRESCOR_DIARIO.md`.
>
> **Regra de leitura:** `status == 200` NÃO prova sucesso em 4 das fontes abaixo. Antes de escrever
> qualquer coletor, ler o catálogo de armadilhas.

## 3. Fontes — matriz de decisão medida

### 3.0 A base legal NÃO é uniforme — cada fonte tem a sua

A crítica adversarial derrubou a apresentação anterior, que invocava o art. 8º da Lei 9.610/98 para
tudo. Correto é **por fonte**:

| fonte | base legal correta | por quê |
|---|---|---|
| Decisão judicial, ementa, súmula | **Lei 9.610/98, art. 8º, IV** | são atos oficiais — sem proteção autoral |
| Texto de lei, decreto, IN | **art. 8º, I e IV** | idem |
| **Informativo do STF (F1)** | **a licença expressa do próprio STF**, com URL e data de consulta: *"Permite-se a reprodução desta publicação, no todo ou em parte, sem alteração do conteúdo, desde que citada a fonte"* (`portal.stf.jus.br/textos/verTexto.asp?servico=informativoSTF`, consultado 2026-08-20) | **"Tese" e "Resumo" são texto editorial** redigido pela Secretaria de Documentação — **não** é obviamente ato oficial. O art. 8º sozinho **não cobre F1** |
| Notícia institucional de tribunal | **não coberta** — só o **fato** é livre | a redação é protegida (art. 7º) |
| Portal privado (Jusbrasil, Migalhas, ConJur, JOTA) | **proibido reproduzir** | protegido; termos vedam expressamente |

**Regra:** a proveniência de cada página registra **qual** base legal a autoriza — nunca um art. 8º
genérico. Onde a base for licença, ela entra com URL e data.

### 3.0-bis Risco contratual do DOU — nomeado, não escondido

O `in.gov.br` tem `robots.txt` = `Disallow: /` **e** termo de uso que veda scraper e finalidade
comercial. A natureza do risco **não é direito autoral** (os atos são públicos) — é
**inadimplemento de termo de uso**, praticado por um advogado inscrito na OAB, num portal que tem
CTA de contratação. O art. 8º não toca essa categoria.

A decisão do dono (2026-08-20) autoriza o acesso como uso próprio identificado. A crítica levantou
um ponto legítimo: **um pipeline diário, automatizado e não supervisionado não é "uso humano"**.
Portanto, para F9 (DOU), o plano fixa:

- o DOU **não entra na Fase 2**; fica na Fase 3, depois de F1–F4 provarem o pipeline;
- quando entrar, é com **volume baixo, ritmo humano e seleção estrita** (só `artType` de alto valor
  jurídico), nunca varredura das 2.956 matérias diárias;
- o registro do risco fica em `docs/data-sources/`, com o veredito do dono, por escrito.

Legenda de robots medida por mim hoje. **Volume medido**, não estimado.

| # | Fonte | Canal medido | robots | Volume/dia medido | Veredito |
|---|---|---|---|---|---|
| F1 | **Informativo STF** — XLSX `Dados_InformativosSTF.xlsx` | 9,3 MB, **11.582 linhas × 24 col.** (Título, **Tese**, **Resumo**, Ramo do Direito, Matéria, Legislação); `Last-Modified` + `ETag` reais | UA de navegador exigido | **~9 itens/semana** (1,2/dia útil) | 🟢 **prioridade 1** — ver base legal em §3.0 |
| F2 | **STJ — dados abertos CKAN** | `temas.csv` 2.391 linhas (1.182 com `teseFirmada`); DJe `metadadosAAAAMMDD.json` + `textos*.zip` | `Crawl-Delay: 10`; `/api/` vedado | **4.680 documentos/dia** no DJe | 🟢 **prioridade 1** — **CC-BY** |
| F3 | ~~STJ — feeds Atom~~ | 346 KB / 88 KB / 18 KB | **`Disallow: /`** | — | 🔴 **FECHADO — ver §3.3** |
| F4 | **normas.leg.br** (LexML/Senado) | JSON-LD schema.org/`Legislation`, ~0,25 s; cliente **já existe** no repo | **`Allow: /`** | ~1,3–2,25 normas/dia | 🟢 **prioridade 1** — **CC-BY 4.0** |
| F5 | **Súmulas STF** `sumariosumulas.asp` | **736 súmulas + 63 vinculantes**, HTML por súmula | `Disallow: /processos` apenas | acervo + novas | 🟢 |
| F6 | **Diários estaduais — 5 UFs com API JSON** (AM, ES, GO, MT, PR) | `GET {host}/apifront/portal/edicoes/edicoes_from_data/AAAA-MM-DD` + PDF | **sem robots** (404) | **~7 edições / ~500 páginas** por dia útil | 🟢 |
| F7 | **Querido Diário** (`api.queridodiario.ok.org.br`) | API JSON + **texto já extraído**; código **MIT** | uso previsto | **295 diários/dia**, 228 municípios, 17 UFs | 🟢 |
| F8 | **Sigpub** (`diariomunicipal.com.br`) | 36 portais de associações estaduais | **`Disallow:` vazio = livre** | medir na Fase 3 desta sessão | 🟢 |
| F9 | **DOU** (`www.in.gov.br/leiturajornal`) | JSON embutido `<script id="params">`; íntegra em `/web/dou/-/{slug}` | **`Disallow: /`** + termo veda scraper | **2.956 matérias/dia** (DO1 346 · DO2 689 · DO3 1.921) | 🟡 ritmo humano, seleção estrita |
| F10 | **DataJud CNJ** | 91 aliases, **352.539.344 docs** | — | lag **6–41 dias**, carga em lote | 🔴 **ver §3.1** |
| F11 | TST (backend REST aberto) · TRFs · notícias oficiais | medido nos dossiês | — | TST via `jurisprudencia-backend2` sem auth | 🟢 Fase 3 desta sessão |

**Vetado por ordem do dono:** INLABS (exige cadastro) — *"não me mande fazer nada de autenticação"*.

### 3.1 DataJud — por que sai da rota principal (decisão com dado)

A API **funciona** e é ampla (91 tribunais, 352 milhões de documentos, chave pública do CNJ). Ela sai
da rota principal por três medições, não por dificuldade:

1. **Não tem texto.** O censo de campos (`_field_caps`) devolve número, classe, assuntos, órgão,
   movimentos e datas — **sem partes, sem advogados, sem ementa, sem íntegra**. É índice de
   movimentação processual, não acervo de jurisprudência: não dá para escrever conteúdo a partir dele.
2. ~~**Termo de Uso, cláusulas 3.3 e 3.8**~~ — **RAZÃO RETIRADA em 2026-09-05, por ordem do dono,
   e ela estava errada.** Termo de uso de API pública não revoga a publicidade constitucional do
   ato judicial: CF art. 5º LX, 37 *caput* e 93 IX; CPC art. 189; Lei 12.527/2011; Res. CNJ
   121/2010 art. 2º. Processo é ato público, e usar dado público de API pública brasileira é
   livre — é o que JusBrasil e Escavador fazem há mais de uma década. O "aceito tacitamente pelo
   uso" era interpretação nossa, não fato jurídico. Some-se que a citação da 3.8 aqui vinha com
   uma ressalva de "autorização prévia por escrito" que **a cláusula não contém** (conferido no
   PDF oficial V1.2, sha256 `2b974d5e…`; quem prevê autorização é a 3.13, e só para o teto de
   requisições). **O que continua sendo limite é técnico**: as 120 req/min da 3.13, que o
   limitador de `internal/datajudfila` já respeita.
3. **Não é fresco.** Lag de 6 a 41 dias por tribunal; carga em lote (TJDFT: 148.480 docs em 10/08 e
   **zero** em 07, 08, 09).

**Substituição, não desistência:** o que o DataJud não entrega — jurisprudência **com texto e
recente** — vem de F1 (Informativo STF, com tese e resumo), F2 (STJ DJe, íntegras CC-BY) e F3
(feeds do STJ). O DataJud fica reservado para **estatística agregada** (ex.: volume de processos por
assunto e tribunal) e para **consulta a pedido de quem tem interesse no processo**, que é o uso
que a ordem do dono de 2026-09-05 liberou. O parecer sobre 3.3/3.8 deixa de ser condição de uso
e passa a ser documentação da posição — o dossiê está em
`docs/goal/DOSSIE_DATAJUD_CLAUSULAS_3_3_E_3_8.md`, com as cláusulas no texto oficial.

### 3.2 Feeds RSS/Atom medidos — o motor do frescor diário

Todos **200, sem auth, sub-segundo**, medidos em 2026-08-20:

| feed | bytes | itens | volume/dia | natureza |
|---|---|---|---|---|
| `processo.stj.jus.br/jurisprudencia/externo/InformativoFeed` | 346.300 | **930** | — | **decisão judicial = domínio público** |
| `scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed` | 88.042 | 281 | — | idem (ISO-8859-1) |
| `scon.stj.jus.br/SCON/PesquisaProntaFeed` | 18.043 | 23 | — | idem (ISO-8859-1) |
| `res.stj.jus.br/hrestp-c-portalp/RSS.xml` | 583.766 | 118 | **4–12/dia útil** | notícia institucional |
| `www.tst.jus.br/rss` | 86.454 | 10 | **8–11/dia** | notícia institucional |
| `www.cjf.jus.br/cjf/noticias/ultimas-noticias/RSS` | 16.082 | 30 | 5–8/dia | notícia institucional |
| `portal.trf6.jus.br/feed/` | 88.845 | 10 | ~6/dia | notícia institucional |
| `agenciabrasil.ebc.com.br/rss/justica/feed.xml` | 53.009 | 10 | ~10/24 h | notícia — **ver licença** |

**Regra de licença para notícia (decisão fixada):** decisão judicial e ato oficial são domínio
público (art. 8º, IV). **Notícia institucional não é** — a redação é protegida, o **fato** não.
Portanto: notícia entra como **fato reescrito autoralmente com link para a fonte**, nunca cópia
nem paráfrase mecânica.

**Correção medida sobre a EBC:** a licença "CC BY 3.0 BR" **não se confirma** — zero ocorrências de
Creative Commons na home, `/sobre` e `/justica`; `/licenca-creative-commons` → **404**. O termo
vigente autoriza reprodução "para veículos de comunicação com fins jornalísticos, mediante indicação
da fonte" e exige contato de licenciamento para **fins comerciais**. Como o portal tem CTA,
**texto da EBC não é reproduzido** — apenas o fato.

**Hosts que negam este servidor** (medido): `jurisprudencia.stf.jus.br` e `redir.stf.jus.br` → 202
(WAF challenge); `www.tse.jus.br` → 403 até no `robots.txt` — política de crawl ilegível, **não
rastrear**; TRF1–TRF5 sem feed válido (200 com `text/html`). O STF **é** alcançável pela via de
arquivo (§F1/F5) desde que se corrija a cadeia TLS incompleta (baixar o intermediário AIA) — dois
agentes divergiram aqui e prevalece a medição mais profunda, que reproduziu o download.

**TST — achado:** `jurisprudencia.tst.jus.br/robots.txt` é `Disallow: /` e o site é SPA sem HTML
rastreável, **mas** o backend `jurisprudencia-backend2.tst.jus.br/rest/*` responde JSON **sem auth**
(`orgaos-judicantes`, `classes-processuais`, `indicadores`). Súmulas, OJs e PNs do TST saem por ali.

**Nada é descartado.** Fonte 🟡, 🔴 ou ⏳ permanece no plano com task própria de investigação.

---

## 3.9 ★ Catálogo de armadilhas por fonte — o achado mais caro da investigação

Cada linha abaixo custou tokens e foi medida por um agente. **São elas que quebram um coletor
ingênuo**, e nenhuma é dedutível da documentação. Este catálogo vai para
`docs/data-sources/FONTES_DIARIAS.md` e é leitura obrigatória de quem implementar cada coletor.

**Regra transversal que aparece em 4 fontes distintas: `status == 200` NÃO prova sucesso.**

### F1 — Informativo STF (XLSX)
- **Coluna G é serial Excel** (época 1899-12-30): `46239,125 → 2026-08-05`. Tratada como texto, vira
  `.125`/`3334` em qualquer histograma.
- `sheet1.xml` usa **`inlineStr`, sem `sharedStrings`** — parser que só lê `sharedStrings` devolve
  **vazio**, silenciosamente.
- **`.htm` da edição nova é 404**: `informativo1222.htm` = 200, `1223`/`1224` = 404. O HTML atrasa
  ~2 edições — para as recentes, citar o **PDF/DOCX**.
- Coluna N (Tese Julgado) vem **vazia** em parte das linhas — célula ausente ≠ coluna ausente.
- **Soft-404 no portal**: caminho inexistente devolve **200 com exatamente 54.429 bytes**
  (md5 `6272f469…`). Comparar tamanho/hash, nunca só o status.

### F2 — STJ dados abertos (CKAN)
- **Cada arquivo diário é um recurso NOVO com UUID novo** — a URL de amanhã é **imprevisível**. O
  coletor precisa reler o HTML do dataset todo dia, e o atalho `/api/` é **vedado por robots**.
- A página `integras-…` custa **11,4 s e 4,1 MB** — pior latência medida; quebra timeout ingênuo.
- `Crawl-Delay: 10` é piso, respeitado por limitador em processo (nunca `sleep`).
- `temas.csv` tem vírgulas e quebras **dentro** dos campos — exige parser CSV real, nunca `split(',')`.
- `situacao` tem 12 valores com **quase-homônimos distintos** (`Cancelada` 335 × `Cancelado` 197):
  agrupar por igualdade de string **inventa categoria**.
- **`textos*.zip` traz nome civil real de pessoa física** (medido) — enquanto `metadados*.json` vem
  anonimizado. É a maior exposição LGPD do conjunto.

### F4 — normas.leg.br
- **Fail-open com HTTP 200**: URN inexistente → **200** com 51 bytes; URN inválida → **200** com 25.
  Coletor ingênuo grava corpo vazio como sucesso. **Validar `legislationIdentifier` na resposta.**
- **`encoding` é dict OU array** — dict quando há uma redação, array quando há várias.
  `json.Unmarshal` em `[]` quebra em metade dos casos.
- O binário é **HTML gerado por Aspose.Words a partir de DOCX**: strip-tags ingênuo traz
  `<o:DocumentProperties>` com **nome da pessoa que editou o arquivo** — dado pessoal de terceiro,
  a descartar sempre.
- `contentUrl` vem como `/api/binario/…`; o caminho público é **`/api/public/binario/…`**.
- **Sitemap ≠ frescor**: ~1 semana de atraso medida (a Lei 15.490 de 17/08 não estava nele).
- Não existe endpoint público de **busca por data** — a URN vem por outro canal.

### F6 — Diários estaduais (AM, ES, GO, MT, PR)
- **O erro volta HTTP 200** com `{"erro":true}` — status 200 não é sucesso.
- Só aceita `YYYY-MM-DD`; `19-08-2026` e `19/08/2026` falham (com 200).
- `paginas` do JSON **não bate** com o PDF (MT declarou 24, o PDF tinha 5).
- **PR**: `www.documentos.dioe.pr.gov.br` serve certificado de outro CN → falha TLS. Host correto é
  `www.dioe.pr.gov.br`.
- **RJ**: `doweb.rj.gov.br` é **NXDOMAIN** (host de tutoriais antigos); vivo é `www.ioerj.com.br`.
- **CE e PI**: porta 443 fechada, só HTTP, charset **ISO-8859-1** → mojibake se assumir UTF-8.
- **PE**: `www.` dá handshake failure; o apex funciona.
- **AM**: recência irregular — zero edições em 18 e 19/08, mas edição em 14/08.
  **Ausência de item ≠ ausência de diário.**

### F7 — Querido Diário
- O host real da API é **`api.queridodiario.ok.org.br`**; `queridodiario.ok.org.br/api/*` devolve
  **200 com o HTML do SPA** para qualquer caminho. **Validar `content_type`, não status.**
- **A chave de frescor é `scraped_since`, não `published_since`** — o robô roda de madrugada sobre o
  dia anterior (ciclo D-1). Pedir "hoje" colhe **quase nada**.
- **`total_gazettes` satura em exatamente 10.000** (teto do Elasticsearch, não contagem).
- `aggregates.file_path` vem **sem barra**: `data.queridodiario.ok.braggregates/...`.
- `.txt` e `.pdf` vêm como `binary/octet-stream`.
- Cobertura em **queda de ~35 % em 14 meses**; **955 de 5.570 municípios** têm alguma coleta (17,1 %).

### F9 — DOU
- `robots.txt` = **`Disallow: /`** e termo veda scraper e uso comercial (§3.0-bis).
- O WAF **só aceita UA com prefixo `Mozilla/5.0`** — UA que se identifica como bot recebe conexão
  fechada (status 000), não 403.
- `content` do JSON embutido é **prévia truncada em 403 caracteres** (328 de 346 idênticas) — a
  íntegra só na página da matéria.
- Sábado, domingo e feriado: `jsonArray` **vazio** — normal, não erro.

### Concorrentes (fonte de pauta, nunca de texto)
- **Migalhas**: `…/{slug}.md` devolve **200 com `text/html`** de 221 KB — soft-200; um coletor
  ingênuo grava HTML achando que é markdown.
- **JOTA**: o corpo vive em `__NEXT_DATA__` com `<p>` escapados (`<p`) — quem extrai por `<p>`
  colhe **1 parágrafo** e conclui "página vazia".
- **news-sitemap é janela móvel** (~2 dias no JOTA, ~10 no Migalhas): perdeu o dia, perdeu a URL.
- **Jusbrasil**: `robots.txt` responde 200 e **todo o resto é 403** — falsa sensação de abertura.

## 3.10 ★ Bugs pré-existentes achados na investigação — todos entram no escopo

Ordem do dono: *"achado de subagente é trabalho pago, tem que ser resolvido; se tiver bug,
aproveitar e corrigir"*. Nenhum destes foi procurado — todos apareceram no caminho, e **todos são
corrigidos nesta sessão**:

| # | bug | arquivo:linha | gravidade |
|---|---|---|---|
| B1 | **`checked_at` é `time.Now()`** — 9.710 páginas afirmam verificação que não houve | `internal/v2publish/v2publish.go:251` | **P0 ético** |
| B2 | `approved_at`/`datePublished` reescritos a cada republicação — não existe data de primeira publicação | `internal/publicrelease/publicrelease.go:496` | **P0** |
| B3 | **Extrator de HTML quebrado**: `DefaultPythonBinary = "python3"`, e o `python3` do sistema **não tem trafilatura**; o venv só é alcançável por flag que nenhum código resolve | `internal/demandtextextractor` | **P0** (silencioso) |
| B4 | **Fetcher sem nenhuma guarda**: sem robots, sem rate limit, sem proteção SSRF, lendo 64 MB | `cmd/enumerate-federal-norms/fetch.go` | **P1 segurança** |
| B5 | **Contradição de política de UA**: um coletor usa UA de navegador para vencer WAF; outro declara *"Nunca se passa por navegador"* | `tools/generate-legal-corpus:25` × `cmd/enumerate-federal-norms/fetch.go:11` | **P1 contrato** |
| B6 | **Comentário que mente**: diz que `newAccessLoggerInDir` serve para "instância paralela", mas a função é **unexported** e ninguém de fora a alcança | `internal/httpserver/access_log.go:115-117` | P2 (R1 do contrato) |
| B7 | **Skill induz erro de leitura de 38×**: manda "nunca somar linhas" — certo para a borda, **errado para a origem** | `.claude/skills/medir-bots/SKILL.md:7-16` | **P1** (já mordeu) |
| B8 | **Nenhum leitor canônico soma a série de origem**, embora o produtor documente a regra | `tools/generate-bot-traffic-origin:70-85` sem consumidor | **P1** |
| B9 | **`feed.RenderRSS` existe, tem teste, e nada o publica** — canal morto | `internal/feed/feed.go:255` | P2 |
| B10 | **`internal/crawleridentity` é Googlebot-only** e **não é importado pelo `httpserver`** — verificação de identidade em runtime não existe | `internal/crawleridentity/identity.go:53,610` | P2 |
| B11 | **Unit "verde" com finalidade 100 % falha**: `edge-warm` fecha `exit 0`, ledger com `failures: 0`, e no mesmo registro `cache_status.miss: 10.004` | `ops/systemd/wikijuridica-edge-warm.*` | **P1** |
| B12 | **Nenhuma unit tem `OnFailure`** — falha com exit ≥2 ou crash não avisa ninguém | `ops/systemd/*.service` (zero ocorrências) | **P1** |
| B13 | **Evidência de IP não se propaga entre agentes**: 97 requisições `amzn-searchbot` dos **mesmos IPs já provados** como scanner caem em `unverifiable` em vez de `forged` | `tools/botagents.py` | P2 |
| B14 | **Faixas de IP upstream defasadas** — bingbot de **2024-01-03**; e 22 agentes sem faixa nem rDNS | `data/ops/bot_ip_ranges/*.json` | P2 |
| B15 | **Rollback sem retenção**: 67 snapshots × 98 MB = 6,2 GB, copiando `pages.json` inteiro para um delta de 15 páginas | `cmd/publish-v2-direct/main.go:2657` | P2 |
| B16 | **301 servidos a bot**: 15 de 68 requisições do Bingbot (22 %) viram redirect — orçamento de rastreio desperdiçado | rota | P2 |
| B17 | **Datas contraditórias na mesma URL**: `dateModified` (06/08) **anterior** a `datePublished` (20/08) no JSON-LD, e o sitemap discordando de ambos | `internal/structureddata` + `internal/sitemap` | **P1 SEO** |

**Regra que vale durante toda a implementação:** achado de subagente **não vira backlog**. Bug
encontrado no caminho é corrigido no mesmo ciclo, com o `arquivo:linha` e a medição registrados no
commit. Se a correção não couber no ciclo, ela vira task **com dono e prazo dentro desta sessão** —
nunca "documentado e seguimos".



## Correção medida em 2026-08-20, depois do levantamento: os feeds do STJ estão FECHADOS

O levantamento inicial mediu `processo.stj.jus.br/.../InformativoFeed` (930 entries),
`scon.stj.jus.br/SCON/JurisprudenciaEmTesesFeed` (281) e `PesquisaProntaFeed` (23) como
**200, sem auth, sub-segundo** — e concluiu "livre". A conclusão estava errada, e quem a
derrubou foi o coletor, ao recusar a requisição:

```
https://processo.stj.jus.br/robots.txt   -> 302
       segue para /processo/robots.txt   -> 200
       "# STJ BLOQUEIOS GERAIS PARA TODOS OS ROBÔS Rev 20250501"
       User-agent: *
       Disallow: /
```

**`Disallow: /` alcança o host inteiro, feed incluído.** O 200 do feed não é permissão —
é só o servidor respondendo. Permissão se lê no robots, e o robots estava num redirect
que o levantamento não seguiu.

De quebra: o `id` de cada entry aponta para `ww2.stj.jus.br/.../INFJ0897`, que redireciona
para **404**. O feed serviria para saber QUE existe a edição, nunca para ler o conteúdo.

**O canal aberto do STJ é o CKAN**, e este está medido e em uso:

| host | robots | veredito |
|---|---|---|
| `processo.stj.jus.br` | **`Disallow: /`** | 🔴 fechado (feeds inclusive) |
| `dadosabertos.web.stj.jus.br` | bloqueia só `/api/`, `/revision/`, `/dataset/rate/`, `/dataset/*/history`; `Crawl-Delay: 10` | 🟢 **em uso** — 1.182 teses firmadas, CC-BY |
| `scon.stj.jus.br` | robots 404 | 🟡 sem política declarada |
| `res.stj.jus.br` | robots 403 | 🟡 política ilegível |

**Lição para os próximos coletores: `robots.txt` que responde 302 precisa ser SEGUIDO.**
Ler o status da URL original e parar ali dá a resposta errada.


## ★ A armadilha que apareceu nas TRÊS fontes: campo que não existe não reclama, só some

Ao implementar os três primeiros coletores, o mesmo defeito apareceu três vezes, com
assinatura idêntica e **nenhum erro lançado em nenhuma delas**:

| fonte | o que pedi | o que existe | sintoma |
|---|---|---|---|
| **STF** (XLSX) | posição por ordem de aparição | posição no atributo `r` da célula | `relator: "Plenário"`, `ramo_direito: "Sim"` — **valor real na coluna errada** |
| **STJ** (CSV) | `titulo`, `ramo` | `questaoSubmetidaAJulgamento`, `Assuntos` | **0 de 1.182** preenchidos |
| **LexML** (JSON-LD) | `description`, `name` | `abstract`, `headline` | **0 de 8** preenchidos |

O XLSX é o pior dos três, porque produz **dado plausível e errado**: o STF omite célula
vazia, então `<c r="A5">…</c><c r="C5">…</c>` não tem `B5`, e acumular por ordem desloca
tudo a partir da primeira lacuna. Nada quebra — o relator simplesmente vira o órgão.

**Regra que fica para todo coletor novo:** imprimir a **taxa de preenchimento por campo**
na primeira execução, assim:

```
titulo          : 8/8
ementa          : 0/8      <- mapeamento errado até prova em contrário
```

Um zero nessa coluna nunca é "a fonte não tem o dado": é o nome do campo que está errado.
E a conferência é sempre contra a **amostra real impressa**, nunca contra o código de saída
— os três coletores fecharam com `exit 0` e a mensagem "registros gravados" enquanto
gravavam campo vazio.
