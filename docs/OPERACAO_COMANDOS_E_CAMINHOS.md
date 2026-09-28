# Operação: comandos, caminhos e arquitetura que enganam

Referência de bancada. Cada item abaixo custou tempo real de sessão — não é
teoria, é o que já deu errado. Consulte ANTES de rodar comando, de ler dado ou
de concluir qualquer coisa sobre a topologia.

Irmãos: `docs/ARQUITETURA_FIEL.md` (topologia e o que cada sonda alcança),
`docs/DADOS_CONFIAVEIS_E_ARMADILHAS.md` (armadilhas de dado por arquivo),
`docs/CONTRATO_DADO_REAL.md` (as dez regras vinculantes).

---

## 1. Comandos que fazem coisa diferente do que parece

| Comando | O que acontece de verdade |
|---|---|
| `./tools/go-modern build ./...` | **Não expande.** `var/nginx/{body,fastcgi,proxy,scgi}` pertence a `nobody` com modo 0700 e o caminhador aborta o padrão inteiro: `pattern ./...: open var/nginx/body: permission denied`. Use `./internal/... ./cmd/...` — medido, não encolhe escopo: as 751 pastas com fonte Go do módulo estão todas ali. |
| `./tools/go-modern run ./cmd/check` | **Sem argumento roda TODOS os gates.** Uma vez abriu 45 processos e levou o load a 52. Para descobrir o nome de um check, leia a fonte — não "tente" o runner. |
| `pgrep -f <padrão>` | Casa **o próprio comando** que você acabou de rodar. Já produziu falso positivo cinco vezes numa sessão, uma delas quase reportando binário vulnerável como em execução. Use `pgrep -x`, `pidof`, ou `systemctl show -p MainPID`. |
| `comando \| tail` | O `$?` é do `tail`, não do comando. **Sempre `${PIPESTATUS[0]}`.** Já fez um teste de regressão parecer aprovado quando reprovava. |
| `curl -A 'wikijuridica-superficie-probe/1.0' https://www.planalto.gov.br/...` | **Devolve `curl (56) Recv failure: Connection reset by peer` e HTTP 000 — e a fonte NÃO está fora do ar.** O WAF do gov.br recusa User-Agent que não comece por `Mozilla/5.0 (compatible; `. Com `-A 'Mozilla/5.0 (compatible; WikiJuridicaBot/1.0; +https://wikijuridica.com.br/sobre/)'` a mesma URL responde **206**, no mesmo minuto. Essa sonda serve para o PRÓPRIO portal; para fonte externa use o UA do `internal/sourcecollect`. O diagnóstico errado chegou a virar bug catalogado ("Planalto inacessível deste host", BUG-161) sobre a fonte que responde por **70,5%** do acervo. |
| `curl https://portal.stf.jus.br/` | `SSL certificate problem: unable to get local issuer certificate` — **não é CA do sistema faltando**: o STF serve o certificado folha duas vezes e nenhum intermediário, e o navegador só não sofre porque busca o intermediário pelo campo AIA. O `internal/sourcecollect` tem remendo de cadeia TLS por host para isso. Com `-k` ele ainda devolve **403**, que aí sim é recusa. |
| `cp novo bin/em-execucao` | Falha com `Text file busy`, e o restart sobe o binário **antigo** reportando sucesso. Use `mv` (rename é atômico) e confira `sha256sum /proc/$(systemctl show -p MainPID --value UNIT)/exe`. |
| `git add … && git commit …` | O pre-commit reprova com `arquivo mudou durante compilação: .git/index`. **Separe em duas invocações.** Mensagem sempre por `-F arquivo`, nunca `-m` com texto longo. |
| `grep 'api/v1/lote'` para achar rota | O código usa **constantes** (`lotePath`), não strings literais. Procure o símbolo, não o texto da URL. Concluí que uma rota estava órfã quando estava ligada. |

---

## 2. Portas e quem serve o quê

```
Cloudflare Tunnel  →  nginx do wiki 127.0.0.1:8088  →  Go 127.0.0.1:8089
                          (root public/, try_files)      (só rota dinâmica)
```

- **O acervo NÃO passa pelo Go.** 10 mil páginas saem estáticas do disco pelo
  nginx. Por isso `data/ops/access/*.jsonl` — que é o ledger **do processo Go** —
  não registra o rastreio do acervo, e concluir "o Googlebot não veio" a partir
  dele é erro garantido. Já aconteceu.
- `8080`/`8081` são do projeto vizinho e não podem colidir.
- `check-portal-health` sonda **só `127.0.0.1`**: ele passa verde com o túnel
  caído. Não serve como prova de que o site está no ar.

---

## 3. O canal Markdown (100% do tráfego de bot de IA)

**Não existe arquivo `.md` em `public/`** — `find public -name '*.md'` devolve
zero. O canal é rota dinâmica do Go (`internal/httpserver/markdown.go`), com
cache próprio em `var/on-demand-cache` e `s-maxage=3600` na borda.

Ele tem **duas portas, e testar uma não testa a outra**:

1. **Negociação**: mesma URL da página HTML, com `Accept: text/markdown`. URL
   **sem** extensão.
2. **Gêmea**: `/caminho/index.md`. URL **com** extensão.

Em 2026-08-27 uma allowlist de extensão no nginx derrubou a porta 2 enquanto a
porta 1 continuava verde — e a regressão só apareceu porque outro gate tropeçou
nela. `tools/check-paridade-go-nginx` existe para isso: compara o que o Go
responde em `:8089` com o que o nginx entrega em `:8088`, e rota que o Go serve
com 200 e o nginx não entrega é sempre defeito.

Só a gêmea emite `Link: rel="cite-as"` (RFC 8574) — na URL que negocia, o
`rel="canonical"` já diz tudo e o cite-as seria redundante. Isso é design, não
bug.

---

## 4. Chaves que enganam a leitura do dado

| Você vai procurar | O nome real |
|---|---|
| `intent_id` no `published_manifest` | **`unique_intent_id`** |
| `path` num registro de `v2_pages` | **não existe** — a rota deriva do `intent_id` |
| `sections[].body` | **`sections[].text`** |
| `faq[].question` / `faq[].answer` | **`faq[].q`** / **`faq[].a`** |
| corpo da página numa chave `text` | é `opening` + `sections[].text` + FAQ, concatenados |

**`word_count` inclui os headings das seções.** A fórmula canônica é
`bodyWordCount` em `internal/v2ingest/validate.go:1011`: abertura + heading +
texto de cada seção + Q e A do FAQ, com tolerância de 10%. Contar sem os
headings acusa divergência que não existe — já produziu 12 falsos positivos numa
conferência.

**Ausência de linha ≠ ausência do fato.** O ledger de borda é cumulativo
intradiário: só o último snapshot de cada par (data, agente) conta, e o leitor
canônico é `serie_saneada`.

---

## 5. Coleta diária: duas armadilhas de semântica

**`scraped_since` NÃO é `published_since`.** O comentário em
`cmd/collect-diarios-municipais/main.go:21` avisa, e ainda assim erramos: pedir
`--desde 2026-08-26` traz o que foi **raspado** desde então, majoritariamente
edições publicadas dias antes. Estimar "251 edições de 26/08 perdidas" a partir
do nome do arquivo produziu uma urgência falsa — a base tinha 3 publicadas
naquele dia.

**Os arquivos diários são COMPLEMENTARES, não cumulativos.** Entre
`2026-08-26.jsonl` e `2026-08-27.jsonl` há 55 registros só no novo e 95 só no
antigo. O `Glob("*.jsonl")` sem filtro de data do gerador é **o que preserva a
união** — "corrigi-lo" para ler só o arquivo do dia encolhe a cobertura.

**`-limite` era o teto da rodada e truncava em silêncio; desde 2026-09-04 é o
TAMANHO DA PÁGINA.** O aviso que morava nesta linha — "um arquivo com exatamente
300 registros é sinal de teto batido" — descrevia um estado que deixou de
existir, e mantê-lo mandaria procurar a assinatura errada.

Por que mudou: as 300 vinham ordenadas por `descending_date`, e a marca d'água
do acervo (`max(scraped_at)` do que se grava) subia para o maior instante de
ingestão entre elas. As edições cortadas, cujo `scraped_at` se espalha por toda
a janela, ficavam abaixo da marca nova e **nunca mais eram pedidas**.

O que procurar agora: a rodada pagina por `offset` até esgotar a janela, com o
corte congelado por `scraped_until`. Janela que **não** esgota — teto de 12
páginas, teto de `offset` do OpenSearch (10.000), ou fonte que declara mais do
que entrega — faz a rodada falhar **sem gravar nada**, para que a marca d'água
fique parada e a rodada seguinte peça a mesma janela. Arquivo do dia com
exatamente `-limite` registros não é mais sinal de nada; o sinal é a linha
`JANELA NAO ESGOTADA` no ledger de coleta, e a resposta a ela é elevar
`-limite` (`tools/run-daily-content:313` passa 300) ou estreitar a janela com
`-desde`.

---

## 6. Coisas que expiram — e quem as colhe

Expiração sem dono vira falha catastrófica em data marcada. O padrão a procurar:
**a entrada é automática, a saída não é.**

| Janela | Prazo | Quem colhe |
|---|---|---|
| Shard de sitemap em carência | 8 dias | `tools/sweep-sitemap-carencia-expirada`, no `ExecStartPre` do servidor |
| Evidência de fonte oficial | 60 dias (90 em parte do acervo; 365 máx.) | `tools/generate-source-live-evidence-recheck`, timer diário 05:40 — **depois** do refresco do inventário das 04:20 |

**Quem manda é `official_source_url_live_metadata_attempts.jsonl`.** O
`official_source_url_live_evidence.jsonl` é **derivado**: `GenerateAt` o
reconstrói inteiro a partir do inventário + das tentativas, toda vez que roda.
Produtor que grave no derivado tem o trabalho descartado na passada seguinte —
foi o defeito corrigido em 2026-09-05, quando o revalidador de TTL sondava as
URLs e reescrevia o arquivo derivado enquanto o refresco diário o reconstruía.

**E `checked_at` do derivado nem sempre é medição.** Sem tentativa válida, o
agregado grava `checked_at = run_date` — um carimbo do lote, com
`http_status_code: 0` e status `..._missing_blocked`. Medido em 2026-09-05:
**6.022 dos 6.421 registros** estão nesse estado. Consequência: um detector de
vencimento que só subtraia datas sobre o derivado responde "zero vencidos" todo
dia, para sempre, porque no dia em que a medição vence a passada das 04:20 já
reescreveu o carimbo para hoje. Só é medição o registro com status
`..._attempted_blocked` ou `..._failed_blocked`.

```bash
./tools/check-official-source-url-live-evidence-ttl-horizon           # censo e agenda de vencimento
./tools/check-official-source-url-live-evidence-ttl-horizon --hoje 2026-10-04
./tools/check-official-source-url-live-evidence-ttl-horizon --falhar-se-divergir
```

Somente leitura, sem rede. Medido em 2026-09-05: 399 registros com medição real,
o primeiro vencimento em **2026-10-04** (40 registros) e o segundo em 2026-11-03
(359). O `--falhar-se-divergir` é o guarda da família: ele acusa qualquer
produtor que volte a gravar medição na camada derivada.

**HEAD não basta para sondar fonte oficial — e ignorar isso fabrica dado
errado.** Medido em 27/08 contra `https://www.gov.br/pt-br/temas/meu-inss`:

```
HEAD + UA próprio ......... 403
HEAD sem UA custom ........ 403
GET com range de 1 byte ... 206
GET + Accept: text/html ... 206
```

O WAF recusa o **método**, não o agente. Uma sonda que só tenta HEAD grava 403 e
o registro passa a dizer "fora do ar" quando a URL está viva — trocar "não medi"
por "está morto" é a pior espécie de dado errado, porque tem cara de medição.
É também a explicação do `206` nos registros antigos: eles usavam GET+Range.

Regra: HEAD primeiro (mais barato), GET pedindo **um byte** quando vier 403 ou
405. Um byte confirma vida sem ler conteúdo, e nada do corpo fica.

Desde 2026-09-05 a regra mora em Go, com teste:
`internal/sourcefetch.shouldFallbackToRangeGET` faz o fallback em 202, 403, 405,
500, 502, 503, 504, 501 e no 520 da Cloudflare, e
`internal/sourceliveevidence` a liga com `AllowRangeGetFallback = true` e
`AllowPlainGetFallback = false`. A sonda em `curl` que existia no revalidador
Python foi aposentada junto com a escrita no arquivo derivado — não porque a
lição estivesse errada, mas porque a medição precisa entrar pela camada que
manda.

O caso do sitemap é o exemplar: `publishedmanifest.Validate` roda **no boot** e
recusa shard fora do índice cuja carência venceu. O comentário no código é
explícito — *"reprovar aqui não é um aviso: é o portal fora do ar"*. A varredura
existia só dentro do `publish-v2-direct`, então a limpeza dependia de alguém
publicar.

A varredura **nunca apaga às cegas**: confere que as URLs do shard estão
cobertas pelo plano vivo, e se alguma ficou órfã ela recusa e mantém — apagar
criaria o 404 que a carência existia para evitar.

---

## 7. Compressão: a gêmea `.br` pode servir corpo velho

`brotli_static on` serve `$uri.br` **sem comparar frescor com o fonte**. Gêmea
desatualizada = corpo antigo com 200 e ETag válido, distribuído pela Cloudflare.

Por isso o gerador de brotli **espera a trava** em vez de sair limpo: quem a
detém enumerou os arquivos quando começou, e se o publish reescreveu HTMLs
depois, o snapshot dela é anterior. Um fail-open ali custou 10.299 gêmeas velhas
em 26/08.

Conferência rápida de gêmea velha:

```bash
python3 -c "
import os,glob
v=sum(1 for br in glob.glob('public/**/*.br',recursive=True)
      if os.path.exists(br[:-3]) and os.path.getmtime(br)<os.path.getmtime(br[:-3]))
print('gemeas velhas:',v)"
```

---

## 8. `public/` é gitignored — e agora tem porteiro

Não há cópia de segurança de nada em `public/`. Duas consequências:

1. **`os.RemoveAll(public/)` apaga o que o build não recria**: 40 cartões
   sociais, 33 `llms.txt`, `feed.xml`, `rss.xml`, `security.txt`, favicons,
   `50x.html`. Foi corrigido em `internal/build/build.go`, mas o comando segue
   documentado — não o rode achando que é idempotente.
2. **Todo arquivo ali vira URL pública.** Havia um `robots.txt.bak` com política
   de crawl obsoleta sendo servido com 200 e cache de sete dias. Hoje o nginx
   tem allowlist (`html|md|ico|png|svg|txt|xml|json` — **sem `br` e sem `css`**,
   conferido em `ops/nginx/standalone/nginx.conf:1623`; a gêmea `.br` sai por
   `brotli_static`, que serve `$uri.br` sem que a URL `.br` seja pedida) e
   `tools/check-public-sem-lixo` reprova extensão inesperada. A folha de estilo
   é a exceção de UMA URL: `location ^~ /assets/` aninha
   `~ "^/assets/wj-[0-9a-f]{16}\.css$"` e devolve **404 para todo o resto do
   diretório** — o gate espelha as duas regras desde 2026-09-04, e tem prova em
   `tools/test_check_public_sem_lixo.py`.

Antes de remover qualquer coisa de `public/`, **arquive** — em
`.agents/runtime/archives/`, com data no nome.

---

## 8b. SEMPRE existe untracked — e ele é cego para você

**Ordem do dono, 2026-08-27**: *"sempre tem untracked e sempre investigar, pois
pode ser algo valioso. E não deixar os untrackeds cegos para os nossos agentes e
claude code."*

O modo de falha é específico e traiçoeiro: um agente de IA lê `git status`, vê
uma pilha de `??` e trata como ruído de fundo. Não é. Naquele dia, o que estava
invisível era:

| Arquivo | O que era de verdade |
|---|---|
| `uta.json` | **20 prefixos IPv6 de crawler do Google** — dado de verificação de bot, com nome que não diz nada |
| `data/research/daily/normas-federais/2026-08-27.jsonl` | 60 linhas de pesquisa do dia |
| `data/research/daily/noticias-oficiais/2026-08-27.jsonl` | 171 linhas de pesquisa do dia |
| `nginx.conf.pre-porteiro-backup` | única cópia da config anterior a uma mudança de produção |
| `owner_alerts_state.json.lock` | esse sim, efêmero |

Quatro dos cinco eram produto. Um deles com **25 horas** de idade.

**O gate `./tools/check-untracked-product-inventory` já existia e já reprovava**
— com a idade em segundos e a classificação (`PRODUTO_STALE`, `untracked_efemero`).
Ninguém o invocava. Gate que existe e não roda é igual a gate que não existe.

Regra de bancada:

1. **Todo `??` é investigado**, nunca presumido ruído. Abra o arquivo, veja o
   tamanho, procure quem o referencia.
2. **Produto vai para o commit** da própria frente, na sessão em que nasce.
3. **Efêmero vai para o `.gitignore`**, classificado com o porquê — **nunca
   deletado**.
4. **Arquivo que é a única cópia de algo** (backup de config, texto redigido) vai
   para `.agents/runtime/archives/` com data no nome, antes de qualquer coisa.
5. Nome obscuro não é licença para ignorar: `uta.json` parecia lixo e era o mapa
   de IPs do Google.

---

## 8c. `GET /mcp` devolvendo 405 é o protocolo, não defeito

Havia 1.031 GETs rejeitados em 10 dias no `/mcp`, de diretórios e monitores
(`SentinelOracle`, `mcpbeat`), e duas propostas no repositório para "consertar"
isso. Nenhuma tinha aberto a spec.

A spec do Streamable HTTP (MCP 2025-06-18, §Listening for Messages from the
Server, item 3) é normativa e diz o contrário:

> The server **MUST** either return `Content-Type: text/event-stream` in
> response to this HTTP GET, **or else return HTTP 405 Method Not Allowed**,
> indicating that the server does not offer an SSE stream at this endpoint.

Medido em produção — estamos conformes nos quatro pontos:

```
GET  /mcp  → 405, com Allow: POST (a RFC 9110 exige o Allow num 405)
           → corpo JSON-RPC estruturado, erro -32600
POST /mcp  → 200, o caminho normativo funciona
```

Quem sonda com GET e conclui "não existe" está errado sobre a spec. **Não há o
que corrigir aqui**, e "consertar" seria abrir um stream SSE que este servidor
não precisa manter. Antes de tratar rejeição repetida como defeito, leia a
especificação: às vezes o número alto é conformidade.

---

## 8d. Gate órfão não é gate morto — triar antes de aposentar

Medido em 2026-08-27, com método declarado (varredura de referências em timers,
hooks, `run-daily-content`, `publicar`, scripts e `cmd/*`, contando invocação
direta e por nome):

```
432 scripts check-*  →  121 com gatilho, 311 ÓRFÃOS (72%)
322 nomes em Names   →    3 com gatilho, 319 órfãos (99%)
```

O "98 órfãos" que circulava era outra coisa — a lacuna script-vs-registro
(421−322), taxonomia diferente de "nunca invocado". O problema real é **três
vezes maior**.

**Mas órfão ≠ morto, e confundir os dois destrói proteção.** Duas provas do
mesmo dia:

- **`check-ingress-security-headers`** foi lido como "bugado, aposentar". Não
  estava bugado: estava **desatualizado** em três pontos (probe não copiava a
  config viva, não carregava os módulos `headers-more`/`brotli`, e tinha uma
  expectativa invertida que **punia uma melhoria**). Consertado, ele vai de 44
  verificações com 1 falha para **52 com zero**. Aposentá-lo teria removido a
  única prova automática de que os oito headers de segurança saem do ingresso.

- **Os 21 `check-codex2-*`** foram sugeridos para aposentadoria em bloco, por
  serem do pipeline desativado em 2026-07-21. Triados um a um: **10 passam**, 3
  reprovam, 1 erra — e o dado que auditam
  (`data/research/codex2_source_live_recheck.jsonl`, 135 linhas) **é vivo**, e
  referenciado pelo gate de evidência de fonte. Aposentar em bloco teria
  desligado dez gates saudáveis.

Antes de aposentar qualquer gate: **rode-o**. Passa? Mede dado que existe? Se
sim, é órfão a ligar, não morto a enterrar. A pergunta certa não é "quem o
chama?" — é "o que ele protege, e isso ainda existe?".

---

## 9. Sondagem: nunca com User-Agent de bot real

Emitir requisição fingindo ser GPTBot, Googlebot ou ClaudeBot é **fraude com
consequência legal** e contamina a própria telemetria do projeto. A forma certa:

```bash
curl -s -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' <url>
```

Aquecimento entra marcado e **fora** da contagem de tráfego. Métrica reflete só
tráfego real.

---

## 10. Antes de commitar página v2

**Dois commits, nesta ordem**: `data/editorial/portfolio_v2/` primeiro,
`data/editorial/v2_pages/` depois. O gate recusa página cujo `intent_id` não
esteja no portfólio do commit **PAI** — uma candidata não pode adicionar a
própria linha de portfólio e consumi-la na mesma transação.

Rode `./tools/check-v2-portfolio-pairing` (read-only, < 1 s, sem build) **antes**
de tentar: cada tentativa cega custa um pre-commit inteiro.

Página escrita **nunca** é descartada. Reprovada se conserta, por gerador
datado, nunca editando JSONL à mão e nunca deletando registro.

## 11. Mexeu em pacote do fecho do ingest? Reateste ANTES de publicar

**O sintoma:** `tools/deploy-publico` morre no **passo 0/7**, antes de qualquer
coisa ir para o ar, com

```
ingest-v2-stock: generated validator attestation does not match authenticated
source graph: generated=sha256:… source=sha256:…; run go generate ./internal/v2ingest
```

**O que é.** `internal/v2ingest` carrega um hash do próprio código de validação
em `validator_fingerprint_attestation_generated.go`. Ele existe para impedir que
um binário antigo alegue estar validando o fonte novo — sem isso, um executável
desatualizado calcularia e afirmaria o hash de um código que não é o dele.

**A armadilha é o ESCOPO do hash.** Ele não cobre só `internal/v2ingest`: cobre
o **fecho transitivo de imports** a partir de `internal/v2ingest` e
`cmd/ingest-v2-stock` — **94 pacotes do projeto**, medidos em 2026-08-27. Entre
eles estão pacotes que ninguém associa a ingestão:

```
internal/content   internal/structureddata   internal/seo   internal/socialcard
```

Ou seja: mexer na **identidade editorial** (`content/site.json` e o struct que a
carrega) desloca a atestação do ingest, e **nada no caminho avisa** — o build
passa, os testes passam, o commit passa, e a descoberta acontece quando o deploy
morre. Foi assim que a publicação dos perfis sociais parou no passo 0.

**O conserto**, que é o que a própria mensagem indica:

```bash
./tools/go-modern generate ./internal/v2ingest
git add internal/v2ingest/validator_fingerprint_attestation_generated.go
flock /tmp/opt-wiki-agent-heavy.lock git commit -F <mensagem>
```

**Confira uma coisa ANTES de regerar:** que a worktree esteja limpa nos pacotes
do fecho. Reatestar com trabalho não-commitado de outra sessão no meio carimba
esse trabalho como estado autenticado.

```bash
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock \
  | grep '^portaljuridico/' > /tmp/fecho.txt
git status --porcelain -- internal/ cmd/ | awk '{print $2}' | sed 's|/[^/]*$||' \
  | sort -u | while read d; do grep -q "portaljuridico/$d\$" /tmp/fecho.txt && echo "SUJO: $d"; done
```

Saída vazia = pode reatestar. O valor gerado tem de bater com o `source=` que o
erro do ingest mostrou; se bater, o atestado é que estava velho — o código não
estava errado.

## 12. Shard de sitemap dando 410 é o desenho, não defeito

**O sintoma que chega:** o Search Console mostra que o Googlebot pediu
`/sitemaps/pages-00NN.xml` e recebeu **410 Gone**.

**Antes de tratar como bug, meça três coisas** — em 2026-08-27 o relato foi sobre
o `pages-0032.xml`, e ele estava **saudável**: 200 na origem, 200 na borda, e
28×200 + 8×304 + **zero 410** no log dos dois dias disponíveis.

```bash
# 1. o shard existe em disco?
ls -l public/sitemaps/pages-00NN.xml

# 2. o que a ORIGEM registrou (o log é a evidência primária)
sudo grep -ah 'pages-00NN\.xml' /var/log/nginx/wikijuridica/access.log{,.1} \
  | grep -oE '"(GET|HEAD) [^"]*" [0-9]{3}' | awk '{print $NF}' | sort | uniq -c

# 3. o que a BORDA serve agora
curl -sI -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
  https://wikijuridica.com.br/sitemaps/pages-00NN.xml | grep -iE 'HTTP|cf-cache|age'
```

**Duas armadilhas de leitura.** O Search Console reporta **com atraso** e lê a
**borda**, não a origem — um GONE de dias atrás não descreve o estado de agora.
E o log cobre ~2 dias: a conclusão honesta é *"sem 410 no log disponível"*, nunca
*"nunca deu 410"*.

**Por que shards somem.** A partição é `ShardPartitionAreaRevision` — a coorte é
**(dia de revisão, área)** — e o ordinal em `pages-%04d.xml` é **posicional
global**, nunca reinicia por grupo. Coorte que esvazia, que é fundida por cair
abaixo do piso, ou cuja soma de miúdas cruza o piso, **desloca todos os ordinais
seguintes**. O total oscila: o portal já teve **≥46 shards** (há pedido de bot a
`pages-0046.xml` no log) e tem **35** hoje. Ordinal alto deixa de existir e passa
a responder 410.

**O 410 está certo** (`ops/nginx/wikijuridica.conf:779-780`): 404 é "não achei,
talvez volte" e mantém a URL na fila de recrawl; 410 é "foi embora", e o crawler
a retira. E a condição é **derivada do disco**, não lista literal — ordinal que
ressuscita volta a ser servido sozinho, sem intervenção.

**O defeito real é o churn de ordinal, e o maior causador já foi corrigido**
(`ef716a9b`, 2026-08-27): as hubs de área e a paginação são re-datadas todo dia
por construção e, enquanto participavam da chave `(data, área)`, drenavam as
coortes do dia anterior, disparavam o coalesce e deslocavam o plano inteiro.
`tools/check-sitemap-shard-churn` mede o deslocamento **antes** de publicar —
rode-o quando um lote grande de revisão se concentrar numa área.

**O que NÃO fazer:** renomear os shards para URLs estáveis
(`{área}-{revisão}.xml`) para acabar com o churn. Isso mataria as **35 URLs
vivas de uma vez** — o incidente multiplicado por 35. O crawler indexa por
`<loc>`, não por nome de arquivo: churn custa **refetch**, não indexação. Se o
churn re-medir alto depois da correção da navegação, aí é frente própria, com
plano de migração. Também não estenda a carência indefinidamente nem sirva 200
para shard morto — sitemap que mente é pior que sitemap que encolhe.

## 13. O número do shard vem do registry — e um registry incompleto derruba o boot

Desde **2026-08-28**, `data/ops/sitemap_shard_registry.json` decide o nome de
cada shard de sitemap. Antes o nome era a **posição** no plano, e por isso
qualquer coorte que nascesse, morresse ou fosse fundida deslocava o ordinal de
tudo que vinha depois — `pages-0034.xml` virou `pages-0018.xml` entre as
publicações de 26 e 27/08.

**O que muda para quem opera:**

| situação | o que fazer |
|---|---|
| vai reiniciar `wikijuridica-server` | `./tools/go-modern run ./cmd/seed-sitemap-registry --root . --verificar` **antes** |
| a publicação parou dizendo que aposentaria N shards | leia o motivo: quase sempre significa que a **data de revisão** mudou em massa, não o acervo |
| algo deu errado e você quer desligar tudo | **renomeie o arquivo do registry.** Sem ele o plano volta a ser o posicional de sempre, byte a byte, sem recompilar |

**Por que o boot pode cair, e por que isso é proposital.** `internal/httpserver`
e `internal/build` são produtores **somente-leitura**: coorte que o registry não
conhece faz `PlanShards` devolver **erro**, e o servidor recusa subir. A
alternativa — deixar o servidor inventar o número — é literalmente o incidente de
2026-08-06, em que publicador e servidor descreveram o mesmo acervo com dois
sitemaps diferentes. Errar alto e cedo é melhor que divergir em silêncio, e o
gate no `deploy-publico` existe para que o erro nunca chegue ao boot.

**Só `cmd/publish-v2-direct` atribui número**, e salva o registry **antes** dos
artefatos: número tem de existir no registry antes de aparecer num arquivo
servido. Se a transação abortar depois disso, sobra um ordinal reservado e não
usado — desperdiçar um ordinal é barato; servir um que o registry não conhece
não é.

**Shard aposentado não perde o número na hora.** Ele fica em `retired` e mantém o
ordinal durante os 8 dias de carência (`sitemapgrace.Period`), porque nesse
período o arquivo ainda serve 200 fora do índice — aquela URL nunca respondeu
4xx. Coorte que volte no prazo recupera o mesmo número, e isso é **continuidade**,
não reuso. Só depois da carência o número vai para `tombstones`, e daí não volta
nunca mais.

## 13b. Mudou a CSP? O nginx precisa de reload, e o sintoma é silêncio total

Medido em 2026-08-28, ao vivo, durante a instalação da API do Clarity.

O acervo foi republicado com o script novo. O `ops/nginx/security-headers.conf` já
tinha o hash novo, propagado por `./tools/go-modern run ./cmd/generate-csp-nginx`.
E mesmo assim, por vários minutos, **a origem serviu um script que o próprio
header recusava**: o nginx só relê a configuração no reload, e ninguém o
recarregou.

O sintoma é o pior possível: **nenhum**. A página responde 200, o HTML está
completo, o conteúdo aparece — o navegador simplesmente se recusa a executar o
`<script>`, em silêncio. Morrem juntos a medição de audiência **e a superfície de
agente WebMCP**, porque as duas metades vivem na mesma constante. Painel vazio é
indistinguível de "não há visitantes"; agente sem ferramenta é indistinguível de
"nenhum agente veio".

Todos os gates da camada passavam verdes nesse estado. O teste de drift compara Go
com `.conf`, o `check-analytics-contract` compara o corpo do script com a constante
Go — e nenhum dos dois pergunta o que o navegador pergunta: *o header que veio COM
esta resposta autoriza o script que veio NELA?*

```bash
./tools/check-csp-hash-servido                    # origem local, 3 rotas
./tools/check-csp-hash-servido --rotas / /familia/ /buscar/ /privacidade/
```

Ele sonda a origem viva, extrai o `<script>` sem atributo da resposta, recalcula o
sha256 e confere contra os hashes do header **da mesma resposta**. Foi ele que
apanhou a janela; `sudo nginx -c … -t` seguido de `systemctl reload
wikijuridica-nginx` fechou; a reverificação em seis rotas passou.

`tools/deploy-publico` faz esse reload sozinho, mas **só quando `INGRESS_MUDOU=1`**,
e isso depende de `ops/nginx/security-headers.conf` estar em
`WIKI_NGINX_CONF_FONTES` (`ops/ingress.env:50`). Está — verificado. Quem publicar
por fora do deploy, ou mexer nessa lista, herda a armadilha.

## 14. Código de saída de ferramenta: 1 é veredito, ≥2 é instrumento quebrado

Auditoria de **2026-08-28** nas 26 units. A regra, que agora vale para toda
ferramenta nova:

- **`exit 1` = VEREDITO MEDIDO** — "medi e encontrei o que existo para
  encontrar". A unit **mascara** com `SuccessExitStatus`, porque alertar em
  veredito vira ruído e mata o canal de alarme por excesso.
- **`exit ≥ 2` = NÃO CONSEGUI MEDIR** — arquivo ausente, JSON inválido,
  credencial faltando, API fora, sonda que não completou. A unit **não** mascara,
  e o dono é avisado.

Misturar os dois no mesmo código é o defeito: enquanto a ferramenta mistura,
**nenhuma configuração de unit fica certa**. Foi assim que
`measure-crawl-coverage` saía 1 por falha de consulta à API — o comentário da
própria ferramenta dizia que ela sai 1 para que "medidor quebrado não passe
despercebido", e a unit mascarava exatamente esse 1.

Cuidado com **trap em `EXIT`**: `run-daily-content` chamava `exit 1`
incondicionalmente no trap e apagava qualquer `exit 2` no caminho de saída — a
correção estaria escrita e seria anulada dois passos depois.

## 13c. As duas leituras externas: quem responde o quê, e o que some se não coletar

Desde 2026-08-29 há credencial para as duas, e elas **não são intercambiáveis**.

| Ferramenta | Responde | Some se não coletar? |
|---|---|---|
| `tools/collect-clarity-insights` | o que a pessoa **fez** na página: sessões humanas × bot, scroll, tempo ativo, rage/dead click | **Sim.** Retenção de 30 dias e janela de 1 a 3 dias na API — o que passou não volta |
| `tools/collect-bing-webmaster` | quantas vezes o acervo **apareceu** numa busca, para qual consulta, em que posição, e quantas páginas estão no índice | Não some, mas o Bing **revisa** dias recentes, e só a série própria preserva a revisão |

Nenhuma outra fonte do projeto responde a segunda pergunta. Origem e borda medem
quem chegou; GA4 e Clarity medem o que a pessoa fez depois de chegar. O Bing mede
**quem viu e não clicou**, que é a maior parte.

```bash
./tools/collect-clarity-insights --dias 3 --dimensoes Device
./tools/collect-bing-webmaster
systemctl status wikijuridica-medicao-externa.timer   # roda 06:10, Persistent
```

**As credenciais têm formatos que se confundem, e a confusão custou uma rodada:**
o token do Clarity é um **JWT** (`eyJ…`, com `scope: Data.Export`); a chave do Bing
é **32 hex**. Passar a do Bing ao Clarity devolve **403 com corpo vazio** — que não
diz nada. Foi o formato, não a mensagem de erro, que identificou cada uma.

**Limites que não se contornam:** Clarity 10 requisições por projeto por dia
(cursor em `data/ops/clarity_insights_state.json`), janela de 1 a 3 dias, no
máximo 3 dimensões, e nome de dimensão errado devolve 400 **consumindo uma das
dez** — por isso o vocabulário é fechado na ferramenta.

**Primeira medição, 2026-08-29,** e ela responde a pergunta que motivou instalar
audiência em 27/08, quando o CrUX não tinha dado algum: **há público humano.**
59 sessões humanas em 3 dias (54 PC, 5 mobile) contra 43 de bot, 92 usuários
distintos, scroll médio de 37,66% no mobile. E no Bing: 717 impressões, 15 cliques
em 17 dias, com o índice subindo de 403 para 1.211 páginas em cinco dias.

---

## Armadilhas medidas em 2026-08-29 (caça aos bugs)

Cada uma custou um ciclo real. As que puderam virar gate viraram — o gate está
nomeado ao lado. As demais estão aqui porque não têm detector honesto.

### `git -C <root>` NÃO obedece ao `-C` quando `GIT_DIR` está no ambiente

Gate: **`tools/check-git-invocacao-saneada`** (roda no `pre-commit` quando o
commit toca `.go`, e no `tools/pre-voo`).

```
$ git -C . ls-files -- go.mod '*/go.mod'          # repo de 2 arquivos
go.mod
sub/go.mod

$ GIT_DIR=/opt/wiki/.git git -C . ls-files -- go.mod '*/go.mod'
go.mod
tools/ci/go.mod
tools/duckdbolap/go.mod ...
```

Não houve erro: houve **resposta errada**. O `.githooks/pre-commit` exporta
`GIT_DIR` e `GIT_INDEX_FILE`, e num commit parcial (`git commit -- <paths>`, a
forma sancionada aqui) esse índice contém só HEAD mais o pathspec. Todo gate que
descobre o universo por `git ls-files` e roda sob o hook mede um **recorte** — e
universo que encolhe não fica vermelho, fica **VERDE**, por não ter visto nada.

Use `gitenv.Command(root, ...)` em produção e `gittestenv.Environment()` em
teste. Quando o ambiente herdado **é** a intenção — um gate de segredo que
inspeciona o `diff --cached` do commit em curso —, marque `//gitenv:deliberado`
com a razão.

### `go generate ./...` de dentro do subpacote grava a atestação ERRADA, com exit 0

```
cd internal/v2ingest && go generate ./...     # ERRADO: -root ../.. resolve para o lugar errado
./tools/go-modern generate ./internal/v2ingest/   # CERTO, da raiz
```

A forma errada sai com **exit 0**, grava o arquivo e só denuncia por um
`warning: could not open directory 'internal/v2ingest/internal/v2ingest/'` no
meio da saída. Seis testes reprovam depois, todos com a mesma mensagem de
fingerprint divergente, e o commit é recusado. Um `go generate` que sai 0 e
grava o artefato errado é indistinguível de sucesso para quem lê só o exit code.

### Truncar a saída do BASELINE inverte a conclusão

Ao comparar árvore atual contra worktree do HEAD, `| tail -8` mostrou 3 falhas
onde havia **19**, e fazia uma delas parecer regressão nova quando já existia no
baseline. É o mesmo erro de método de ler série temporal pela janela que o
enunciado escolheu. Baseline se lê **inteiro**, ou se filtra pelo que se quer
contar (`grep -oE ... | sort -u`), nunca pelas últimas N linhas.

### `t.Fatalf` em laço de auditoria audita UM item

O laço que confere ~460 wrappers parava no primeiro achado — que, por acaso do
alfabeto, era falso positivo. Atrás dele ficava escondido o único verdadeiro.
Mostrava **1 violação**; havia **189**. Laço de auditoria **acumula e reporta
todos**; `t.Fatalf` só no fim.

Mesmo desenho do gate de proveniência publicada, que empilhava 10.070 linhas de
bookkeeping e por isso nunca mostrava o defeito de conteúdo que existe para achar.

### Detector textual precisa remover DOCSTRING, não só `#`

138 dos 462 wrappers são Python. Docstring Python não começa com `#`, então um
detector que só descarta comentário de `#` acusa menção em docstring como se
fosse execução. E a invocação real deste repositório muitas vezes passa por
**variável** (`subprocess.run([..., GERADOR, "--write"])`), que nenhum detector
de caminho literal encontra.

Regra: **detector novo nasce com teste de falso positivo sobre amostra real.**
Sem ele, o detector novo repete o erro que veio corrigir — aconteceu duas vezes
no mesmo dia.

### Medir com a chave errada produz número reprodutível e falso

`content/source_registry.json` usa `source_id`, não `id`. Ler `id` devolve
`None` para todas as 58 fontes e faz concluir que o ID curado "não existe" —
conclusão que levaria a "corrigir" código que está certo. Antes de agir sobre
uma medição, confira o **schema** do dado (`list(fontes[0].keys())`).

Irmãs já registradas: `published_manifest` chaveia por `unique_intent_id`;
`.split()` cru não é a fórmula de `word_count` (use `ptbrtext.BodyWords`).

### `>/dev/null` num wrapper engole o erro do próprio wrapper

```sh
com_retry "add" git add -- "$@" >/dev/null || return 1   # ERRADO
```
O redirecionamento apanha também os `echo` de diagnóstico que `com_retry`
imprime, e a falha vira silêncio. Mande diagnóstico para **stderr** (`>&2`)
quando a função puder ter o stdout redirecionado.

### Edição por âncora calculada em arquivo grande

Um `rindex` casou uma ocorrência muito depois da pretendida e truncou um arquivo
de 5.496 para 301 linhas, levando junto trabalho de agente que nunca foi staged
— sem blob no ODB para recuperar.

Guarda: **`~/.claude/hooks/snapshot-antes-de-escrever.py`** (PreToolUse) copia
todo arquivo rastreado com +200 linhas para `.agents/runtime/autosave/` antes de
qualquer escrita — Write/Edit, redirecionamento `>`, `open(...,"w")` em
`python3 -c`, `sed -i`. Leitura por **`tools/recuperar-do-autosave`**, que nunca
restaura sozinho.

E, ao editar por âncora, **valide o tamanho resultante** antes de gravar:
`assert novo > orig*0.9`.

### `git show HEAD:<arquivo> > <arquivo>` não é neutro

Restaurar de HEAD apaga TODO o não commitado daquele arquivo, inclusive
correções de outras frentes feitas horas antes. Só use depois de conferir
`git diff <arquivo>` e de salvar o estado atual.

### Gate sem gatilho é gate cego

461 `tools/check-*` existem; **408 não são chamados por ninguém** (medido
2026-08-29). Gate nasce órfão por construção neste repositório. Ao criar um,
declare o gatilho no mesmo commit: `.githooks/pre-commit` (condicionado ao que o
commit toca), `tools/pre-voo`, ou o registro de `cmd/check`.


## O grafo do validador não é o diretório `internal/v2ingest`

Quem mexe no grafo de fonte do validador tem de reatestar **no mesmo commit**,
senão `ingest-v2-stock` recusa publicar e **nenhum deploy passa** — e a
descoberta acontece minutos depois, dentro do `deploy-publico`, que morre no
passo 0a. Aconteceu cinco vezes, e dos dez commits que tocaram `internal/v2ingest`
em 29/08, **seis eram unicamente re-atestação**.

**A armadilha que faz isso reincidir:** o grafo é a **closure transitiva de
import** a partir de `internal/v2ingest` e `cmd/ingest-v2-stock` — **96 pacotes**
do módulo. O deploy das 21:34 de 29/08 morreu porque um commit tocou
`internal/structureddata`, `internal/legalfacts` e `internal/legalcorpusindex`,
que ninguém associa ao ingest e estão todos no grafo. Uma regra por prefixo de
diretório ("tocou `internal/v2ingest/`") não teria pego nenhum dos três.

```bash
./tools/go-modern list -deps ./internal/v2ingest ./cmd/ingest-v2-stock   # quem está no grafo
./tools/check-atestacao-grafo-no-commit                                  # ligado ao pre-commit
./tools/check-validator-attestation                                      # confere o hash do disco
./tools/go-modern generate ./internal/v2ingest                           # o remédio
```

`check-atestacao-grafo-no-commit` lê **só o índice do commit** e não recalcula o
hash — de propósito. Recalcular leria o DISCO, e o disco de um commit parcial
(`git commit -- <pathspec>`, que este repositório manda usar) tem trabalho de
outras frentes: reprovar por arquivo alheio ainda não commitado seria falso
positivo caro. Custa zero quando o commit não tem Go de produção e zero quando o
atestado já está nele. `_test.go` não entra no grafo
(`validator_fingerprint_graph.go:669`).

## A fábrica tinha uma janela morta de três horas por dia (corrigida, DEC-040)

Até 2026-08-30, `validation_as_of` truncava no dia **UTC** e `legal_as_of` no dia
de **São Paulo**, e `stock_freshness.go:361-364` exige que as duas batam com o
relógio de agora. Resultado medido: **180 minutos por dia**, das 21:00 às 24:00
BRT, sem publicação possível. Às 21:00 BRT o dia UTC virava e um ingest
bem-sucedido de sete horas antes já aparecia como
`v2_stock_freshness_validation_as_of_stale`.

Está corrigido — os dois calendários viram juntos à meia-noite de Brasília. O que
fica como aviso operacional é o **sintoma**, porque ele reaparece com qualquer
outra dessincronia de relógio:

> `v2_stock_freshness_validation_as_of_stale: receipt=X required=Y` com o estoque
> intocado **não é estoque velho**. Compare o dia das duas chaves antes de
> reingerir: se `receipt` e `required` diferem em um dia e nenhum shard mudou, o
> problema é de calendário, não de conteúdo.

E a lição geral, que custou três horas de trabalho para achar: **data pura
(`"2026-07-11"`) não carrega fuso, e `time.Parse` a coloca em UTC.** Onde ela vai
ser comparada com um dia normalizado no fuso brasileiro, use
`time.ParseInLocation(time.DateOnly, valor, legalValidationLocation)` — senão a
data retrocede um dia inteiro em silêncio.

## `git worktree` para medir o pré-existente: ela NÃO carrega o que o `.gitignore` esconde

Montar uma worktree do `HEAD` e rodar o teste lá é o jeito certo de separar
"regressão minha" de "já estava vermelho" — foi assim que se provou, em
2026-08-30, que três testes de `internal/v2sourceresearchreconcile` já falhavam
antes de qualquer mudança.

**Mas o veredito dela só vale para teste que lê o que está versionado.** Medido
na mesma sessão: a worktree acusou **99 falhas** em `internal/v2ingest` que o
repositório real não tinha. A causa não era o código — era o que `git worktree
add` não copia:

```bash
ls data/editorial/v2_pages | wc -l   # repo real: 878   worktree: 876
ls data/source-audit      | wc -l    # repo real:  43   worktree:  40
git status --porcelain --ignored data/ | grep '^!!' | head
#   data/editorial/.tombstone-*.lock, .v2txn-retired-*.tombstone, ...
```

Os tombstones e locks de transação são **ignorados de propósito** e o produto os
lê. Numa worktree limpa eles não existem, e dezenas de validadores de fato
jurídico reprovam por falta de dado — vermelho que parece histórico e é do
método.

**A regra:** worktree isolada é boa para pacote cuja fixture está no git. Quando
o pacote lê `data/` viva, o baseline honesto é o `git log` do teste e a execução
no repositório real — e uma contagem de falhas muito maior na worktree do que no
repo é sinal de dado ausente, não de regressão descoberta.

## O envelope pesado tem DUAS variáveis de tempo, e vence a MENOR

Medido em 2026-08-30, ao tentar regenerar a evidência do `languagetool-quality` sobre 7.959 registros.

`WIKI_HEAVY_TIMEOUT_SECONDS` é a variável que aparece na mensagem de recusa do `run-go-cmd-cached` e a que se encontra lendo `tools/run-heavy-throttled:121`. Passei `1795` e o comando morreu em **120 segundos**. A explicação veio do próprio envelope, e ela é a linha que faltava documentar:

```
run-heavy-throttled: timeout efetivo=120s vindo de WIKI_HEAVY_BUDGET_MS=120000;
o WIKI_HEAVY_TIMEOUT_SECONDS=1795 declarado NAO estava em vigor (vence o menor dos dois).
```

**São duas variáveis independentes** — `WIKI_HEAVY_TIMEOUT_SECONDS` (segundos) e `WIKI_HEAVY_BUDGET_MS` (milissegundos) — e o envelope aplica **o menor dos dois**. Declarar só a primeira dá a impressão de ter aumentado o orçamento e não aumenta nada; o comando morre no prazo da outra, com `exit_code=124`, que é o mesmo código de um timeout legítimo. Para dar mais tempo de verdade, declare **as duas**.

E há um teto acima delas, com a orientação certa embutida:

```
run-go-cmd-cached: WIKI_HEAVY_TIMEOUT_SECONDS must not exceed 1800s;
shard/cache/optimize instead of increasing the timeout
```

**1800 s é o limite duro**, e a mensagem diz o que fazer quando não cabe: fatiar, usar cache ou otimizar — nunca esticar o relógio. Vale ler isso junto com a regra do contrato: lentidão em 10k é bug P0, e aumentar timeout é proibido como conserto. O orçamento maior serve para trabalho que é longo **por natureza** — 7.959 chamadas HTTP a um serviço local —, não para esconder um gerador lento.

**Sinal correlato, que aparece antes do fim:** `progress_monitor_alert status=io_without_progress_risk consecutive_windows=2`. O supervisor percebe I/O sem progresso e avisa em janelas consecutivas. Duas ou três dessas linhas antes de um `exit_code=124` significam que o comando estava vivo e esperando — não travado —, e que o orçamento é que era curto.

## `.git/config` com extensão declarada e `repositoryformatversion=0` cega ferramenta de análise

Medido em 2026-08-30, ao investigar por que o `generate-sca-sbom` cuspia isto em toda execução:

```
WRN failed to determine version of main module
    error="git: core.repositoryformatversion does not support extension: worktreeConfig"
```

O estado do clone era:

```
core.repositoryformatversion = 0
extensions.worktreeConfig    = true      (em .git/config)
.git/worktrees/wt-head/                  (existe)
.git/worktrees/*/config.worktree         (NÃO existe)
```

**A especificação do git é clara:** com `repositoryformatversion = 0`, **nenhuma** extensão pode estar declarada — extensões exigem versão 1. O git nativo tolera a inconsistência e segue funcionando, e é por isso que ela sobrevive despercebida; bibliotecas de terceiros que implementam a especificação à risca (`go-git`, usada pelo `cyclonedx-gomod`) **recusam ler o repositório** e caem em fallback silencioso.

**O que estava em jogo:** o SBOM não conseguia determinar a versão do módulo principal. Um SBOM sem versão do próprio projeto é insumo degradado para toda a cadeia de SCA.

**A correção, e por que ela e não a outra.** Havia duas saídas: subir `repositoryformatversion` para 1, ou remover a extensão. Como **nenhum `config.worktree` existe** — ou seja, ninguém usa configuração por worktree —, a extensão estava declarada sem uso. Removê-la restaura a versão 0, que é universalmente suportada, em vez de empurrar o clone para a versão 1 e arriscar outras ferramentas. O git redeclara a extensão sozinho se alguém rodar `git worktree config`.

```bash
git config --unset extensions.worktreeConfig
```

Conferido depois: `git status`, `git worktree list` (as duas worktrees) e `git log` seguem funcionando.

**★ E o essencial para quem clonar noutra máquina: `.git/config` NÃO é versionado.** Esta correção vale para este clone e mais nenhum. Se o aviso reaparecer, é o mesmo estado — confira `git config --get-all extensions.worktreeConfig` junto com `core.repositoryformatversion` antes de procurar defeito no gerador.

## Armadilhas medidas em 2026-09-02 (restauro do servidor Go)

### A unit do serviço exige um `.socket` — e o socket só sobe DEPOIS do binário

Desde 2026-09-01 `wikijuridica-server.service` tem `Requires=wikijuridica-server.socket`
e `Type=notify`; o binário herda o socket (`cmd/server/main.go`, `escutar`) e manda
`READY=1` só depois do listen. Duas armadilhas, as duas pagas:

- **Unit editada no repo entra em vigor no próximo boot, porque é symlink.** A `.socket`
  ficou sem instalar em `/etc/systemd/system` e o serviço passou 17 h em `failed` com
  `Failed to schedule restart job: Unit wikijuridica-server.socket not found` — toda
  rota dinâmica em 503. Gate: `tools/check-units-instaladas` (agendado na qualidade
  diária); o `--repair` do watchdog instala a dependência ausente antes de reiniciar.
- **Ativar o socket com o binário velho é pior que a falha.** O systemd fica dono da
  porta; o binário sem `LISTEN_FDS` faz bind próprio, falha com EADDRINUSE, e o
  `Restart=always` gira a cada 5 s com a porta em LISTEN: a conexão do nginx entra na
  fila do kernel e vira 504. Medido em 02/09 10:47, 40 s até ser parado à mão — e quem
  disparou foi o watchdog, 30 s depois de a `.socket` ser instalada. Ordem: binário novo
  (`strings bin/wikijuridica-server | grep -c LISTEN_FDS` ≥ 1) → socket → serviço; é o
  que `tools/deploy-publico --sem-republicar` faz. Ao instalar unit à mão, pare antes
  `wikijuridica-watchdog.timer`.

### `--sem-republicar --ressemear` é o restauro barato: sem reingest, sem republicação

`REPUBLICAR=0` pula os passos 0 (reingest, que dispararia porque a atestação do
validador é mais nova que o `stock_manifest`) e 1 (republicação); o passo 2 compila,
o 3 para socket+serviço, o 4 troca o binário, o 5 sobe os dois e prova com `curl`, o 6
purga TUDO (mudança de camada) e reaquece, o 7 faz o smoke. Não purgue à mão depois.

### A Cache Rule guarda 5xx: `status_code_ttl` 0 é *no-cache*, não *no-store*

`0` armazena e serve `STALE`; `-1` é não guardar. Com HTML e Markdown na mesma chave
(`Vary: Accept` normalizado), um GET com `Accept: text/markdown` que recebe 503 derruba
o HTML fresco de 7 dias (`HIT age 1500 → 503 STALE → EXPIRED`, reproduzido 2×). O
aquecedor com o Go caído zerou a cobertura da borda 6×/dia. Cobertura 0 % com
`EXPIRED` em massa depois de queda do Go é isto, não colo, TTL nem eviction.

### O PerplexityBot vem ~1.200 req/dia e as séries dizem "0"

A Cloudflare não verifica a Perplexity; toda série que conta só
`cloudflare_verified_bot_category` o apaga, e o error budget o rotulava como "sonda deste
repo". Identidade por faixa oficial de IP (`data/ops/bot_ip_ranges/perplexitybot.json`,
`clientIP` no GraphQL — janela máxima de 1 dia no plano Free) é a segunda lane.

## `cmd/social-verificar-oab` — deferir a inscrição na OAB de um perfil (2026-09-09)

`internal/verificacaooab.Pedir`/`Deferir` não tinham NENHUM chamador de produção até
2026-09-09 — os cinco usos existentes eram todos `_test.go`. Sem um deles rodar contra
`var/social/social.db`, o selo `advogado_verificado` nunca nasce, e
`internal/socialautoridade.Publicar` (o caminho que a DEC-059 abre para o cérebro
publicar comentário sob a assinatura do responsável técnico) não tem como autorizar
nada. Este comando é o caminho de OPERADOR que faltava — rodado pelo dono, ou pelo
chefe sob ordem dele, nunca por um handler HTTP: deferir inscrição é decisão humana
sobre evidência conferida por gente.

```bash
./tools/go-modern run ./cmd/social-verificar-oab \
  --handle rafaeltoledo --oab 227191 --seccional RJ \
  --evidencia /caminho/para/registro-cna.pdf \
  --revisor "dono:ordem-2026-09-09-DEC-059" \
  --motivo "conferido no Cadastro Nacional dos Advogados em <data>" \
  --dry-run                      # sem --confirmar, nada é escrito
```

- **A KEK nunca é gerada aqui.** Lida de `WIKI_SOCIAL_KEK` no ambiente ou de
  `--env-file /opt/wiki/.env.social` (é ali que a unit a lê, por último; `.env.local` é compartilhado com o `cmd/server` e não a leva); sem ela, exit **2** com a instrução para gerar
  (`./tools/go-modern run ./cmd/generate-social-kek`) e reiniciar o serviço — nunca
  inventa chave.
- **Abre o banco como `verificacaooab_test.go` abre**, não como
  `cmd/social/superficie.go`: `socialdb.Abrir` + `verificacaooab.Migra` +
  `socialconteudo.Novo` + `contas.AbrirNaConexao` sobre o MESMO pool — sem
  `moderacao.Abrir` (que exigiria um `moderacao.Conteudo` e criaria um arquivo de sal
  que este comando não precisa).
- **O handle pedido pode divergir do handle que `GarantePerfilDaConta` deriva** do nome
  público (slug de "Rafael Toledo" = `rafael-toledo`, nunca `rafaeltoledo`) — aquela
  função não aceita handle escolhido, e `internal/socialconteudo` está fora de
  fronteira para este comando. Quando diverge, um `UPDATE perfis SET handle = ...`
  direto renomeia, guardado pelo `UNIQUE` e pelo `CHECK` de tamanho (3–32) do próprio
  esquema — mesmo padrão operacional de `internal/contas/recuperacao.go:140`.
- **`--dry-run` não escreve nada**, nem quando o handle já existe (idempotência lida de
  `perfis_advogado` + `Selo()` + o pedido pendente mais recente, nunca deduzida de
  histórico em memória). Sem `--dry-run` nem `--confirmar`, o comando também não
  escreve — só mostra o plano e sai 1 pedindo uma das duas flags.
- **`--criar-conta`** cadastra a conta e o perfil quando o `--handle` ainda não existe;
  a senha (24+ caracteres, `crypto/rand`) sai UMA vez no stdout do `--confirmar` e
  nunca é gravada em ledger nem em log.
- **O ledger (`data/ops/social_verificacoes_oab.jsonl`) nunca guarda evidência nem
  e-mail** — só o SHA-256 do documento e os campos já públicos no próprio selo.
- Perfil que "parece" ser o do responsável técnico do portal (nome público OU
  OAB/seccional batendo com `content/site.json`) exige que os DOIS lados batam — um só
  lado batendo é recusado, para não deferir inscrição divergente sobre a identidade
  dele.
