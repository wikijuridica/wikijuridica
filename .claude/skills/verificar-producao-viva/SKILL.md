---
name: verificar-producao-viva
description: Use para conferir se o portal está realmente no ar — sondagem que alcança a borda, não só 127.0.0.1.
---

# Verificar a produção viva

## O que cada sonda alcança (e o que ela NÃO vê)

`check-portal-health` sonda **só `127.0.0.1`**. Ele passa **verde com o túnel
caído** — o visitante em 500 e o gate em verde ao mesmo tempo. Nunca conclua
"está no ar" a partir dele.

O acervo **não passa pelo Go**: sai estático do disco pelo nginx. Por isso o
ledger do processo Go não registra o rastreio do acervo.

```
Cloudflare Tunnel → nginx 127.0.0.1:8088 → Go 127.0.0.1:8089
   (5 instâncias)     (root public/, proxy_cache wj_dyn)   (socket do systemd)
```

## A sequência

```
./tools/check-portal-health            # origem: Go + nginx (não vê a borda)
./tools/check-http-smoke               # smoke HTTP
./tools/check-agent-surface-live       # canal de máquina pelo nginx
```

E pela **borda**, que é o que o mundo recebe:

```
curl -sS -o /dev/null -D- https://wikijuridica.com.br/ \
  -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true'
```

O User-Agent de sonda e o header são obrigatórios: sem eles a sonda entra na
métrica e o portal mede o próprio eco. **Nunca** sonde com User-Agent de bot
real — é fraude de métrica, e um hook de máquina barra.

## Confira as três camadas, não uma

1. **Go** (`:8089`) — `/readyz`, journal da unit.
2. **nginx** (`:8088`) — houve 13 min em que o Go respondia e o proxy não. O
   vigia sonda a gêmea Markdown e o agent-card **pelo nginx** por causa disso.
3. **borda** — `age`, `cf-cache-status`. `HIT` com `age: 0` logo após purga
   significa que a borda repopulou com o conteúdo **VELHO**.

Validar config do nginx é `nginx -t` **sem sudo**. Com sudo, `var/nginx/` volta
a `nobody`, os workers tomam EACCES e o canal inteiro vira 500 (um hook barra).

## O dono disse que não funciona

Acredite e investigue mais fundo: o artefato **servido** e a infra, não `curl` no
terminal. Ausência de sinal não é evidência — o detector que você espera ver pode
nunca executar.
