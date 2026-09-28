# AI Performance do Bing Webmaster Tools por API — investigação de 2026-09-15

Alvo: ler por programa as ~23.000 citações que o dono vê no painel de
`wikijuridica.com.br`, para virar rotina no projeto.

---

## VEREDITO EM UMA LINHA

**Não existe método de AI Performance na API pública do Bing Webmaster (a de
`apikey`), e a ausência é declarada pela Microsoft, não deduzida por mim.** O
caminho real para automatizar hoje é o endpoint que o próprio painel usa
(`www.bing.com/webmasters/api/...`), que **autentica por sessão de conta
Microsoft + token anti-forgery — a chave do `.env.local` não serve lá**, e que
portanto se automatiza com o Chromium persistente que o projeto já opera em
`:99`.

---

## (a) O nome do método — e a frase oficial de que ele não existe

### Não existe na API pública

A superfície da API é o *service contract* `IWebmasterApi`. A referência oficial
lista **62 métodos** e **nenhum** contém `AI`, `Copilot`, `Citation`,
`Grounding`, `Generative`, `Chat`, `Answer` ou `LLM`. A página está congelada em
`updated_at: 2023-11-14`, ou seja, nunca foi tocada depois do recurso de
fevereiro de 2026.

Fonte: <https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces.iwebmasterapi>

### A frase oficial, atribuída e datada

**Fabrice Canel (Microsoft, Bing), em 2026-02-11:**

> "With this preview, the data is not yet available via the API. Enabling data in
> our API is on our backlog, and we'll take your feedback along with others, into
> account when prioritizing next release."

- Veiculação: Search Engine Roundtable, 2026-02-11 —
  <https://www.seroundtable.com/bing-webmaster-tools-ai-performance-report-40911.html>
- **Cadeia de custódia honesta:** a citação é **secundária** (SERoundtable
  reportando Canel) e chegou a mim por sumarização de página. Não localizei o
  post original de Canel. Tratar como "declaração da Microsoft reportada por
  veículo especializado", não como documento primário da Microsoft.

**Corroboração independente**, Microsoft Q&A, pergunta de 2026-02-19 intitulada
exatamente "Bing Webmaster Tools AI Performance report. Is there an API?":

> "In the Blog post, no API is mentioned so the answer is not right now. You may
> keep checking https://blogs.bing.com for any updates."

— resposta de *Independent Advisor*, 2026-02-19T11:09:51Z.
<https://learn.microsoft.com/en-us/answers/questions/5780844/bing-webmaster-tools-ai-performance-report-is-ther>

> **Ressalva de valor probatório:** o respondente é *Independent Advisor*, não
> funcionário da Microsoft; e a outra "resposta" da mesma página é uma resposta
> gerada por IA. **Nenhuma das duas é autoridade.** Valem como corroboração de
> que a pergunta foi feita publicamente e não obteve desmentido, nada além.

**Página de ajuda do produto (passo 2 da tarefa), e por que não há citação
dela:** `https://www.bing.com/webmasters/help/ai-performance-9f8e7d6c` é
renderizada por JavaScript. O fetch devolveu **apenas o `<title>`** ("Bing
Webmaster Tools - Help Documentation"), sem corpo de artigo. **Não há frase
citável dali** — é limite do instrumento, não etapa pulada. Quem quiser a frase
precisa abrir a página num navegador (o mesmo Chromium de `:99` resolveria).

O anúncio oficial (2026-02-10,
<https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview>)
descreve as quatro métricas — **Total Citations**, **Average Cited Pages**,
**Grounding Queries**, **Page-level Citation Activity** — e **não menciona API,
exportação programática nem CSV** em nenhuma frase. O silêncio do anúncio é o que
os dois respondentes acima citam como base.

### O que EU medi contra a API viva

Controle positivo, com a chave do `.env.local` e o UA do contrato:

```
GetUserSites -> HTTP 200, 243 bytes
{"d":[{"__type":"Site:#Microsoft.Bing.Webmaster.Api", ... "IsVerified":true,
       "Url":"https://wikijuridica.com.br/"}]}
```

Quatro nomes ainda não testados pelo chamador, derivados do vocabulário do
próprio painel (`aiperformance`, `citationstats`), todos contra
`https://ssl.bing.com/webmaster/api.svc/json/<Metodo>?apikey=…&siteUrl=https://wikijuridica.com.br/`:

| Método | HTTP |
|---|---|
| `GetAIPerformanceCitationStats` | **404** |
| `GetCitationStatsFiltered` | **404** |
| `GetCopilotCitationStats` | **404** |
| `GetAiPerformance` (variação de caixa) | **404** |

**Total acumulado: 28 nomes candidatos, 28 × HTTP 404, contra um controle que
responde 200 na mesma janela.** A conclusão não é "não achei o nome": é que a
operação não existe no contrato WCF servido.

**E OAuth não muda isso.** A documentação de *Getting Started* oferece, além da
`apikey`, OAuth 2.0 com `Bearer` — mas o alvo é **o mesmo serviço `api.svc`**, o
mesmo *service contract* `IWebmasterApi`, os mesmos 62 métodos. OAuth troca a
forma de autenticar, **não acrescenta operação nenhuma**. Não há rota por
credencial melhor.

---

## (b) JSON cru com a nossa chave

**Não se aplica — não há método a chamar.** Nenhum dado de citação é obtenível
com a chave do `.env.local`. As ~23.000 citações do painel **não passam por
`ssl.bing.com/webmaster/api.svc/json`**.

---

## (c) O caminho real para automatizar

### O endpoint do painel

Documentado por terceiro que o capturou do próprio painel (Nick Blazer) —
<https://www.nickblazer.com/blog/ai-citation-data-exports-bing-webmaster-tools/>.
*A data do artigo não veio no fetch; "2026-03" é **inferido** do
`Tue, 24 Mar 2026` que aparece no exemplo de payload dele.*

```
POST https://www.bing.com/webmasters/api/aiperformance/citationstats/filtered/export

accept: application/json, text/javascript, */*; q=0.01
content-type: application/json;charset=UTF-8
x-csrf-token: <token da conta>

{
  "SiteUrl": "https://wikijuridica.com.br/",
  "DateRange": {
    "BeginTimeStamp": "Sat, 01 Nov 2025 00:00:00 GMT",
    "EndTimeStamp":   "Tue, 15 Sep 2026 00:00:00 GMT"
  },
  "Query": "",
  "Page": "https://wikijuridica.com.br/alguma-pagina/"
}
```

- Timestamps em **RFC 1123 / GMT**.
- Resposta: **CSV**, citação diária por página (não JSON).
- **Dado mais antigo disponível: 2025-11-01**, em janela rolante.
- Sobre o `x-csrf-token`, o autor observa: *"I tested the x-csrf-token on
  multiple BWT properties I have access to and it remained the same. It is
  likely connected with your account."*

> **Status probatório deste endpoint: NÃO verificado por mim.** É caminho de
> terceiro, de 2026-03. Ver abaixo por que a verificação é impossível sem
> sessão.

### O que eu provei sobre a autenticação (isto sim é medição própria)

**1. A chave do `.env.local` é inútil no host do painel.** Quatro variantes de
POST — caminho real sem chave, caminho real **com** a chave, caminho inventado, e
caminho real com `x-csrf-token` sintético — devolveram resposta **byte a byte
idêntica**:

```
HTTP 400 — "Origin and Referer request headers are both absent/empty"   (sem Origin/Referer)
HTTP 400 — "Could not extract expected anti-forgery token"              (com Origin/Referer)
```

A chave não muda absolutamente nada. Afirmação exata do que isto prova: **a
chave não dispensa o par anti-forgery** em `www.bing.com/webmasters/api/*`. Se o
roteador atrás do filtro honraria uma apikey é coisa **não medida** (e
implausível) — o filtro nunca deixa a requisição chegar lá.

**2. O filtro anti-forgery roda ANTES do roteamento.** É por isso que o caminho
inventado responde igual ao caminho real — e é por isso que **o meu controle
negativo não discrimina nada**. Registro isto explicitamente: *não provei que
`aiperformance/citationstats/filtered/export` existe no servidor.* A mensagem é
de anti-forgery do ASP.NET (par cookie + cabeçalho `x-csrf-token`).

**3. O painel inteiro é gated por sessão de conta Microsoft.** Medido:

```
GET https://www.bing.com/webmasters/aiperformance?siteUrl=https%3A%2F%2Fwikijuridica.com.br%2F
  -> HTTP 302  location: https://www.bing.com/toolbox/webmaster/?from=aiperformance
  -> set-cookie: ReturnUrl=…%2Fwebmasters%2Faiperformance…   (guarda o destino)
  -> set-cookie: _EDGE_S, _EDGE_V, MUID, MUIDB              (só rastreio, nenhum de auth)
```

**Controle que me corrigiu:** cheguei a ler o `?from=aiperformance` como prova de
que a rota existe. Testei `naoexisteestapagina`, `querystats` e `xyzzy123` no
mesmo lugar: **todos devolvem 302 com o `from=` ecoando o próprio caminho**. O
parâmetro é eco puro. O redirecionamento prova **apenas** que toda a árvore
`/webmasters/*` está atrás de login, e nada sobre o nome da rota.

### Conclusão operacional

Automatizar hoje = **navegador autenticado**. Não há rota por chave, e não há
rota por cabeçalho estático: é preciso um contexto que carregue (i) os cookies de
sessão da conta Microsoft do titular e (ii) um `x-csrf-token` pareado com o
cookie anti-forgery daquela sessão.

**O projeto já tem exatamente essa máquina.** `tools/publicador-social/` roda
`playwright-core` 1.49.1 com perfil Chromium **persistente**, sob
`XDG_STATE_HOME` (`~/.local/state/wikijuridica/perfil-navegador`), em `:99`
(Xvfb), com `perfil.mjs` expondo `WIKI_PERFIL_NAVEGADOR` para forçar outro
caminho. É o mesmo padrão já sancionado para Facebook e LinkedIn. Nada de SaaS,
nada de credencial nova, nada de serviço proprietário.

**Grounding queries:** o payload conhecido tem `Query` e `Page`, o que sugere que
o mesmo endpoint filtra pelos dois lados — **mas isso é inferência, não medida**.
A aba de grounding queries pode ter um "Download all" próprio em caminho irmão. O
caminho real se captura da aba Network na **primeira execução autenticada**, e é
isso que a implementação deve fazer em vez de chutar.

---

## (d) Recomendação de implementação

### Onde fica

Não dentro de `tools/collect-bing-webmaster`. Aquele coletor é HTTP puro com
`urllib`, sem Node, sem navegador, e roda em unit com `timeout 120`. Enfiar
Playwright ali contamina um caminho que hoje é barato e confiável.

**Estrutura proposta:**

- `tools/collect-bing-ai-citations` — executável novo (Python, padrão do
  coletor), que invoca um `.mjs` Playwright e normaliza o CSV para o ledger.
- `tools/coletor-bing-ia/` — o lado Node, espelhando `publicador-social/`:
  `perfil.mjs` (aponta para perfil **separado**), `exportar.mjs`,
  `package.json` com `playwright-core` fixado em `1.49.1`.
- `tools/collect-bing-webmaster` ganha **apenas** uma nota de rodapé apontando
  para o novo coletor, para quem for procurar AI Performance lá.

### Perfil separado, e por quê

Usar `WIKI_PERFIL_NAVEGADOR` para um diretório próprio
(`~/.local/state/wikijuridica/perfil-bing`). **Não misturar a sessão da conta
Microsoft com o perfil que carrega Facebook e LinkedIn**: uma reautenticação ou
uma corrupção de perfil derrubaria as três de uma vez, e a publicação social é
frente que já funciona.

### Token: colher, nunca fixar

**Proibido hardcodar o `x-csrf-token`** do artigo. A cada execução:

1. Abrir `https://www.bing.com/webmasters/aiperformance?siteUrl=…` no contexto
   persistente.
2. `page.on('request')` para interceptar a XHR que o próprio painel dispara e
   **colher o `x-csrf-token` fresco** dali.
3. `page.request.post(...)` — que reutiliza os cookies do contexto — com o token
   colhido.

Assim o coletor não depende de um segredo copiado à mão, e sobrevive à rotação.

### Identidade de saída — tensão real com o §11, declarada

O contrato manda `wikijuridicabot.Aplica` em toda saída. Um Chromium logado numa
conta Microsoft manda UA de navegador; forçar o UA do bot no *login* tende a
quebrar o fluxo. É **a mesma exceção sob a qual o `publicador-social` já vive**.

Regra proposta, e mensurável: UA de navegador **somente** na navegação/login;
no **POST de exportação**, injetar
`Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; observacao-de-citacao-ia)`
via `headers` do `page.request.post` e **medir** se o Bing aceita. Se aceitar,
fica; se recusar, registra-se a recusa medida e a exceção fica documentada como a
do publicador social. Isto precisa entrar em `tools/check-identidade-de-saida`
como exceção **nomeada**, não como omissão — foi ausência de UA que já escapou
daquele gate uma vez (`if not agentes: return [], False`).

### Teto de requisição

**Um run por dia UTC, ≤ 5 requisições.** Justificativa honesta: **o teto do
painel não está medido** — os 10/60 s medidos em 2026-09-09 são de
`ssl.bing.com`, host **diferente**, e não se transferem. Começar conservador,
medir na primeira semana, só então relaxar. Reaproveitar a classe `Ritmo` do
coletor existente.

Janela: como o dado começa em **2025-11-01** e é rolante, a primeira execução
puxa `2025-11-01 → hoje` (carga histórica completa, de uma vez) e as seguintes
puxam uma janela curta de reconciliação (últimos ~7 dias), porque o Bing **revisa
números recentes** — a mesma razão que fez o ledger existente ser append-only.

### Onde grava

Mesmo arquivo e mesmo contrato do coletor atual:
`data/ops/bing_webmaster_daily.jsonl`, `schema: "bing_webmaster_v1"`,
append-only, `coletado_em` em cada linha, linha idêntica não regravada.

Bloco novo: **`citacao_ia_diaria`**, ao lado de `busca_diaria`,
`rastreio_diario`, `consulta_diaria`, `pagina_diaria`, `problema_de_rastreio`.
Se o grounding query tiver endpoint próprio, um segundo bloco
**`consulta_de_grounding`**.

**Os nomes de campo do CSV não são conhecidos** e só se conhecem na primeira
execução autenticada. A normalização se escreve **depois** de ver o cabeçalho
real — escrever o parser antes seria inventar esquema.

### A única dependência que não dá para engenheirar

**O titular precisa autenticar uma vez** a conta Microsoft no perfil `:99`,
exatamente como já fez para Facebook e LinkedIn. Credencial de conta pessoal é a
fronteira que o contrato reserva ao dono; tudo depois disso é automático, e a
sessão persiste no perfil.

### Nota de risco, sem inflar

O endpoint do painel não é documentado e não tem compromisso de estabilidade:
pode mudar sem aviso. O coletor deve **falhar alto e visível** (exit ≠ 0 com o
corpo do erro no cursor), nunca gravar linha vazia que pareça "zero citações" —
ausência de sinal não é evidência. E convém deixar um teste que reprove se o
`x-csrf-token` voltar a ser lido de constante em vez de colhido.

E, quando a Microsoft tirar o item do backlog, **isto vira uma função de 10
linhas dentro de `tools/collect-bing-webmaster`** e o lado Node se aposenta.
Vale acompanhar <https://blogs.bing.com/webmaster>.

---

## O que o advisor mudou

Cinco correções materiais, todas no que o relatório **afirma**:

1. **Derrubou a minha verificação do endpoint.** Eu tinha quatro respostas
   idênticas e ia apresentá-las como sondagem; o advisor apontou que o filtro
   anti-forgery roda antes do roteamento, então o controle negativo **não
   discrimina** e eu **não provei que o caminho existe**. O relatório passou a
   dizer "caminho de terceiro, não verificado por mim".
2. **Mandou medir a autenticação em vez de inferir.** Foi o que produziu o 302
   para `toolbox/webmaster` e a lista de cookies — e, por tabela, o controle
   `naoexisteestapagina`/`xyzzy123` que **me pegou** interpretando
   `?from=aiperformance` como prova de rota. Sem essa ordem eu teria publicado
   uma inferência falsa.
3. **Rebaixou a citação de Canel** de "frase oficial" para fonte secundária
   sumarizada, e vetou usar a "AI answer" do Microsoft Q&A como autoridade.
4. **Exigiu declarar a tensão do UA** no caminho Playwright em vez de passar por
   cima dela, com proposta mensurável em vez de exceção silenciosa.
5. **Apertou o (d)**: perfil Chromium separado, token colhido por interceptação
   (nunca fixo), teto declarado como **não medido** neste host, e campos do CSV
   assumidamente desconhecidos até a primeira execução.

Também orientou a gravar primeiro no caminho sancionado do plano antes de tentar
o caminho pedido — o que foi feito.

**Segunda passada, com o arquivo já no disco**, mais quatro:

6. **Achou um ponto cego:** o passo 2 da tarefa (página de ajuda do produto) não
   aparecia em lugar nenhum do relatório. Silêncio sobre etapa pedida lê-se como
   etapa pulada — entrou parágrafo próprio dizendo que a página é SPA e que o
   fetch só trouxe o `<title>`.
7. **Cortou um exagero meu:** eu escrevera "`?apikey=` não é aceito" quando a
   evidência só alcança a camada anti-forgery — que, como eu mesmo dizia duas
   linhas abaixo, roda antes do roteamento. A afirmação contradizia a própria
   ressalva.
8. **Marcou dois fatos que vieram de memória, não de fonte:** o cargo de Canel
   (removido) e a data do artigo do Nick Blazer (agora explicitamente inferida do
   payload de exemplo).
9. **Mandou antecipar o OAuth**, que de outro modo viraria a primeira pergunta de
   volta.

---

## Fontes

- [IWebmasterApi — referência oficial (updated_at 2023-11-14)](https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces.iwebmasterapi)
- [Anúncio oficial, 2026-02-10](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview)
- [SERoundtable, 2026-02-11 — Fabrice Canel sobre a API](https://www.seroundtable.com/bing-webmaster-tools-ai-performance-report-40911.html)
- [Microsoft Q&A, 2026-02-19 — "Is there an API?"](https://learn.microsoft.com/en-us/answers/questions/5780844/bing-webmaster-tools-ai-performance-report-is-ther)
- [Nick Blazer, 2026-03 — endpoint do painel e payload](https://www.nickblazer.com/blog/ai-citation-data-exports-bing-webmaster-tools/)
- [merj/bing-webmaster-tools — cliente Python, sem nada de AI](https://github.com/merj/bing-webmaster-tools)
- [Getting Started with Webmaster API](https://learn.microsoft.com/en-us/bingwebmaster/getting-started)

Arquivos do projeto relevantes: `/opt/wiki/tools/collect-bing-webmaster`,
`/opt/wiki/tools/publicador-social/perfil.mjs`,
`/opt/wiki/tools/publicador-social/package.json`,
`/opt/wiki/data/ops/bing_webmaster_daily.jsonl`.
