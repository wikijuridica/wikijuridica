---
paths:
  - "ops/nginx/**"
  - "ops/cloudflare/**"
  - "tools/generate-nginx-standalone"
  - "tools/apply-dynamic-redirect-rules"
  - "tools/check-nginx-standalone-parity"
  - "tools/purge-origin-cache"
  - "tools/purge-edge-cache"
  - "tools/check-edge-frescor"
---

# nginx e borda — o vivo e' o standalone, e `-t` com sudo derruba o canal

Memorias de origem: `sudo-nginx-t-chown-nobody.md`,
`arquivo-novo-em-public-duas-allowlists.md`, `cache-rule-5xx-ttl0-derruba-html.md`,
`check-tools-gravar-precedente.md` (a metade sobre o nginx).

Os incidentes medidos (datas, contagens, tempos) estao em
`docs/ops/NGINX_E_BORDA_CASOS.md`, movidos literais em 2026-09-23.

## `sudo nginx -t` re-atribui `var/nginx/` e poe o canal de maquina em 500

`nginx -t` executa `ngx_create_paths` e, sob root, faz `chown` de `var/nginx/cache`
para o usuario da diretiva `user`; os workers (`User=rafael` da unit) tomam EACCES em
todo objeto do `proxy_cache` — gemea Markdown, cards e lote em 500 (2026-09-02). Rode
`-t` como o usuario da unit, sem sudo:

```
/usr/sbin/nginx -c ops/nginx/standalone/nginx.conf -p var/nginx/ -t
```

(o binario nao esta no PATH). A diretiva `user rafael rafael;` no conf torna o
`-t` sob root inofensivo; `tools/check-nginx-runtime-dirs` reprova dono errado;
`check-portal-health` sonda a gemea e o card PELO nginx. Reload:
`sudo -n systemctl reload wikijuridica-nginx`, e conferir 0 `[emerg]` no
`error.log`.

## O `standalone` NASCEU de gerador e hoje se edita A MAO — nunca regenerar

`ops/nginx/standalone/nginx.conf` saiu de `tools/generate-nginx-standalone`
(2026-08-13) e depois recebeu edicoes a mao (`user rafael rafael;`, cabecalho,
brotli/gzip off na gemea): regenerar por cima as DESCARTA. **O vivo e' o
standalone**: mudanca de nginx se faz a mao nos DOIS confs, no mesmo `location`, e
`tools/check-nginx-standalone-parity` (0 linhas perdidas, baseline de 53 conhecidas)
prova a paridade.

## Extensao nova em `public/` passa por DUAS allowlists, as duas por extensao

O standalone (config VIVO; o `wikijuridica.conf` nao tem a regra) devolve 404 para
extensao fora de `location ~* "\.(?!(?:html|md|ico|png|svg|txt|xml|json|gz)$)…"`, e a
borda redireciona 301 para `…ext/` pela regra de barra final de
`ops/cloudflare/dynamic-redirect-rules.json`, que exclui extensoes por lista. As duas
sao de seguranca (barram `.env`, `.bak`, `.br` direto). Ao publicar extensao nova:
(1) a extensao na allowlist do standalone + `nginx -t` sem sudo + reload; (2) a
`.ext` no `not ends_with(...)` da regra de redirect + `apply-dynamic-redirect-rules`
(ledger `data/ops/edge_rule_apply.jsonl`); (3) `tools/purge-edge-cache --url` para as
URLs que ja levaram 404/301 (a borda cacheia o 404).

## O objeto do nginx tem UM ARQUIVO POR VARIANTE, e o nome NAO sai da chave

`Vary: Accept-Encoding` (emitido por `location @fallback` e `@markdown`) faz o nginx
guardar um arquivo por VALOR do cabecalho:

    objeto principal   md5(chave)
    variante           md5( md5_bruto(chave) + b"accept-encoding:" + valor + b"\r\n" )

A variante depende do que o cliente mandou (`ngx_http_file_cache_vary`): quem invalida
por formula apaga o principal e deixa servindo a variante que a borda pede. **A forma
certa e' OBSERVAR, nao adivinhar**: todo objeto carrega `\nKEY: <chave>\n` depois do
cabecalho binario (byte 336 no nginx 1.22.1). `tools/purge-origin-cache` varre a zona,
indexa por chave, remove TODOS os objetos da rota e **confere a ausencia** (sai 2 se
sobrar algum). A varredura e' por CHAMADA: lote e' custo, nao economia. Nao enumere
host/esquema/porta: o `$host` nao carrega porta.

## Purgar a borda com a origem velha e' PIOR que nao purgar

Ordem: `purge-origin-cache` → `purge-edge-cache` → reler — no deploy do binario, na
transacao de publicacao e no vigia de frescor. So' a borda, com o nginx ainda com o
corpo antigo, da MISS servindo o ANTIGO.

## Cache Rule: `status_code_ttl` 0 e' *no-cache*, -1 e' *no-store*

Na Cloudflare `0` armazena e serve STALE; HTML e Markdown partilham a chave por
`Vary: Accept` normalizado, entao um 5xx da origem apagava o HTML da borda. 5xx vai a
`-1` em `ops/cloudflare/cache-rules.json`; o aquecedor sonda `/readyz` da origem antes
da passada Markdown e pula quando != 200. Cobertura 0% com EXPIRED em massa depois de
queda do Go = este mecanismo, nao colo/TTL/eviction.
