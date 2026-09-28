# nginx e borda — casos medidos e parágrafos superados

> Movido de `.claude/rules/nginx-e-borda.md` em 2026-09-23. A rule passou do teto de 6.000
> caracteres que `tools/check-modo-operacional` cobra (T1) e foi condensada para
> veredito, ordem dos passos e comando de medição (plano
> `docs/plans/IDE_TERMINAL_20260923_PLANO.md` §8, frente 4, item 6). **Nada foi
> apagado:** a seção "Texto integral" abaixo é a rule exatamente como estava no commit
> `7e0d8426`, sem o frontmatter `paths:` (que continua na rule). Os casos medidos, as
> tabelas de tempo e os parágrafos marcados SUPERADO ficam aqui como evidência; o que
> vale como ordem é a rule.
>
> Este arquivo não carrega em sessão nenhuma: é lido quando a rule manda ou quando
> alguém precisa do número que sustentou o veredito.

## O que só está aqui

- **2026-09-02, 11:19-11:32** — `sudo -n nginx -t` no deploy: 13 min de 500 na gêmea Markdown, cards e lote (404 truncado em 0 B virava 520 na borda); o vigia dizia OK porque sondava o Go direto.
- **2026-09-09** — o gerador a seco (`--saida /tmp/x`) diverge em 965 linhas do standalone vivo.
- **2026-09-08** — `public/datasets/*.jsonl.gz` no disco com 404 na origem e 301 na borda; a borda cacheou os 404.
- **2026-09-16** — zona `wj_dyn`: 24.933 arquivos para 13.738 chaves (11.189 com mais de um objeto); access.log com 51.217 pedidos `gzip, br` e 40.728 vazios; purga de 11.268 rotas em 5,66 s numa chamada contra ~209 s em lotes de 400; nenhuma chave com `https` nem `:8088`.
- **2026-09-16** — `/noticias/index.md`: só a borda → MISS em 1,11 s com o corpo antigo; origem e depois → MISS em 1,03 s com o corpo do Go; propagação da purga por URL de 0,10 a 0,72 s em oito rotas.
- **2026-09-02** — Cache Rule com 5xx = 0: HTML `HIT age 1500` → `503 STALE` → `EXPIRED`; `warm-edge-cache --markdown` com o Go fora apagou o acervo da borda (40/40 HIT → 40/40 EXPIRED).

## Texto integral da rule até 2026-09-23 (commit `7e0d8426`)

# nginx e borda — o vivo e' o standalone, e `-t` com sudo derruba o canal

Memorias de origem: `sudo-nginx-t-chown-nobody.md`,
`arquivo-novo-em-public-duas-allowlists.md`, `cache-rule-5xx-ttl0-derruba-html.md`,
`check-tools-gravar-precedente.md` (a metade sobre o nginx).

## `sudo nginx -t` re-atribui `var/nginx/` e poe o canal de maquina em 500

Medido em 2026-09-02, 11:19-11:32: o deploy rodou `sudo -n nginx -t` antes do
reload; o nginx, como root, criou/re-atribuiu `var/nginx/cache` a `nobody:0700`;
os workers (`User=rafael` da unit) tomaram EACCES em todo objeto do
`proxy_cache`, e **gemea Markdown, cards e lote responderam 500 por 13 minutos**
(404 truncado em 0 B virava 520 na borda). O vigia dizia OK porque sondava o Go
direto. Causa: `nginx -t` executa `ngx_create_paths` e, sob root, faz `chown`
para o usuario da diretiva `user`.

Rode `-t` como o usuario da unit, sem sudo:

```
/usr/sbin/nginx -c ops/nginx/standalone/nginx.conf -p var/nginx/ -t
```

(o binario nao esta no PATH). A diretiva `user rafael rafael;` no conf torna o
`-t` sob root inofensivo; `tools/check-nginx-runtime-dirs` reprova dono errado;
`check-portal-health` sonda a gemea e o card PELO nginx. Reload:
`sudo -n systemctl reload wikijuridica-nginx`, e conferir 0 `[emerg]` no
`error.log`.

## O `standalone` NASCEU de gerador e hoje se edita A MAO — nunca regenerar

`ops/nginx/standalone/nginx.conf` foi gerado de `ops/nginx/wikijuridica.conf` por
`tools/generate-nginx-standalone` (2026-08-13), mas desde entao recebeu edicoes a
mao (`user rafael rafael;`, cabecalho, brotli/gzip off na gemea). Medido em
2026-09-09: o gerador a seco (`--saida /tmp/x`) diverge em **965 linhas** do
arquivo vivo — regenerar por cima DESCARTARIA essas edicoes. **O vivo e' o
standalone**: mudanca de nginx se faz a mao nos DOIS confs, no mesmo `location`,
e `tools/check-nginx-standalone-parity` (0 linhas perdidas, baseline de 53
conhecidas) e' quem prova a paridade.

## Extensao nova em `public/` passa por DUAS allowlists, as duas por extensao

Em 2026-09-08 os dumps `public/datasets/*.jsonl.gz` existiam no disco e a origem
devolvia 404 — `location ~* "\.(?!(?:html|md|ico|png|svg|txt|xml|json|gz)$)…"
{ return 404; }` em `ops/nginx/standalone/nginx.conf`, que e' o config VIVO (o
`wikijuridica.conf` nao tem essa regra) — e a borda respondia 301 para `…gz/`,
pela regra de barra final em `ops/cloudflare/dynamic-redirect-rules.json`,
aplicada por `tools/apply-dynamic-redirect-rules`, que exclui extensoes por
lista. A borda ainda cacheou os 404.

As duas listas sao de seguranca (barram `.env`, `.bak`, `.br` direto) e ninguem
as lembra ao criar formato novo. Ao publicar extensao nova: (1) a extensao na
allowlist do standalone + `nginx -t` sem sudo + reload; (2) a `.ext` no
`not ends_with(...)` da regra de redirect + `apply-dynamic-redirect-rules`
(ledger `data/ops/edge_rule_apply.jsonl`); (3) `tools/purge-edge-cache --url`
para as URLs que ja levaram 404/301.

## O objeto do nginx tem UM ARQUIVO POR VARIANTE, e o nome NAO sai da chave

Medido em 2026-09-16 na zona viva `wj_dyn`: **24.933 arquivos para 13.738 chaves**,
`{1 objeto: 2.549 chaves, 2: 11.186, 3: 2, 6: 1}` — **11.189 chaves com mais de
um objeto**. A causa e' o `Vary: Accept-Encoding` que `location @fallback` e
`@markdown` emitem: o nginx guarda um arquivo por VALOR do cabecalho.

    objeto principal   md5(chave)
    variante           md5( md5_bruto(chave) + b"accept-encoding:" + valor + b"\r\n" )

A segunda formula foi reproduzida byte a byte (`ngx_http_file_cache_vary`): para
`fb:httpwikijuridica.com.br/noticias/cjf-20260820/index.md:0`, a variante de
`Accept-Encoding: ""` e' `9810fcb2…`, que existe no disco e **nao e' derivavel da
chave sozinha** — depende do que o cliente mandou. Quem invalida por formula
apaga o principal e deixa servindo a variante que a borda de fato pede (medido no
access.log: 51.217 pedidos `gzip, br` e 40.728 vazios).

**A forma certa e' OBSERVAR, nao adivinhar**: todo objeto carrega `\nKEY: <chave>\n`
logo depois do cabecalho binario (byte 336 no nginx 1.22.1). `tools/purge-origin-cache`
varre a zona, indexa por chave, remove TODOS os objetos da rota e **confere a
ausencia** — e sai 2 se sobrar algum. Custo medido: 5,66 s para as 11.268 rotas
dinamicas numa chamada so, contra ~209 s em lotes de 400 (a varredura e' por
CHAMADA, entao lote e' custo, nao economia).

Enumeracao fixa de host/esquema era letra morta: das 13.738 chaves vivas,
**nenhuma** tem `https` e **nenhuma** tem `:8088` (o `$host` do nginx nao carrega
porta); duas tem `127.0.0.1` sem porta, que a lista fixa nunca montava.

## Purgar a borda com a origem velha e' PIOR que nao purgar

Medido em 2026-09-16, `/noticias/index.md`, duas fases na mesma rota:

    so' a borda        MISS em 1,11 s servindo o corpo ANTIGO (o nginx ainda o tinha)
    origem e depois    MISS em 1,03 s servindo o corpo do Go

A ordem e' `purge-origin-cache` → `purge-edge-cache` → reler, e ela vale para o
deploy do binario, para a transacao de publicacao e para o vigia de frescor. A
janela de propagacao da purga por URL foi medida em oito rotas: **0,10 s a
0,72 s** do retorno da API, com a primeira leitura ja `MISS` e fresca.

## Cache Rule: `status_code_ttl` 0 e' *no-cache*, -1 e' *no-store*

Reproduzido 2x em 2026-09-02: HTML `HIT age 1500` -> GET com
`Accept: text/markdown` recebe `503 STALE` -> o mesmo HTML volta `EXPIRED`. A
Cache Rule tinha `status_code_ttl` 500-599 = `0`, que na Cloudflare significa
*no-cache* (armazena e serve STALE), nao *no-store* (`-1`); e HTML e Markdown
partilham a chave por `Vary: Accept` normalizado. `warm-edge-cache --markdown`
6x/dia com o Go fora **apagou o acervo inteiro da borda** (40/40 HIT -> 40/40
EXPIRED).

5xx vai a `-1` em `ops/cloudflare/cache-rules.json`; o aquecedor sonda `/readyz`
da origem antes da passada Markdown e pula quando != 200. Cobertura 0% com
EXPIRED em massa depois de queda do Go = este mecanismo, nao colo/TTL/eviction.
