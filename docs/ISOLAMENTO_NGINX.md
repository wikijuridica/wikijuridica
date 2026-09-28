# Isolamento do nginx — por que, o que já existe e como trocar

## O acoplamento

O portal tem configuração própria (`ops/nginx/wikijuridica.conf`, symlink em
`/etc/nginx/sites-enabled/wikijuridica`), mas divide o **processo** nginx e o
bloco `http {}` de `/etc/nginx/nginx.conf` — arquivo escrito e mantido pelo
projeto vizinho `/opt/divorcio`.

Três consequências, e a segunda já custou tempo real de diagnóstico:

1. Uma configuração quebrada do vizinho reprova `nginx -t` e **bloqueia o reload
   deste site**, mesmo estando tudo correto aqui.
2. Diretiva global do vizinho muda o comportamento daqui sem aviso. Em
   2026-08-06, `open_file_cache max=900000 inactive=900s` (linha 1944 do conf
   global, sem `open_file_cache_valid`) fez o nginx continuar servindo o HTML da
   versão anterior depois de uma republicação — arquivo em disco com 19.855
   bytes, resposta com 19.639, nas páginas mais acessadas.
3. Um `systemctl restart nginx` afeta os dois projetos ao mesmo tempo.

## O que já está pronto

- `ops/nginx/standalone/nginx.conf` — `http {}` autossuficiente: workers, temp
  paths, gzip, log e cache próprios. **Não inclui `sites-enabled/`**, então nada
  do vizinho entra e nada daqui vaza.
- `ops/nginx/standalone/bot-policy.conf` — política de bots e rate limit,
  extraída do vhost para arquivo único, de modo que as duas instâncias nunca
  divirjam.
- `ops/nginx/standalone/server.conf` — o `server {}` do portal.
- `ops/systemd/wikijuridica-nginx.service` — unit da instância dedicada.

### Validação já executada (2026-08-06)

Instância dedicada subida em **8090**, em paralelo à do sistema em 8088:

| verificação | resultado |
|---|---|
| conteúdo de `/`, página jurídica, `/sitemap.xml`, `/robots.txt`, `/50x.html` | **byte a byte idêntico** ao da instância do sistema |
| Googlebot, OAI-SearchBot, ChatGPT-User, Claude-User, PerplexityBot — 60 requisições seguidas | **200 em 60/60**, sem bloqueio |
| custo por requisição para bot | **5–6 ms**, TTFB 0,3 ms, 19.855 bytes |

Bot valioso premia site barato de rastrear — é assim que ele decide reindexar e
citar. O isolamento não pode piorar isso, e não piora.

## Por que ainda não foi trocado

A troca exige liberar a porta 8088 da instância do sistema e assumi-la com a
dedicada. É a única operação desta frente com risco de indisponibilidade, e o
ganho é **preventivo** — hoje o site está estável e a mitigação já aplicada
(`open_file_cache_valid 5s` no vhost + restart do nginx no `deploy-publico`)
cobre o defeito concreto que apareceu.

Trocar junto de outra mudança impediria saber qual delas causou um eventual
problema. Fica para janela dedicada.

## Procedimento de troca

```bash
# 1. Conferir que a dedicada está válida
/usr/sbin/nginx -c /opt/wiki/ops/nginx/standalone/nginx.conf -p /opt/wiki/var/nginx/ -t

# 2. Apontar a dedicada para 8088 (hoje está em 8090 para validação paralela)
sed -i 's|listen 127.0.0.1:8090;|listen 127.0.0.1:8088;|' ops/nginx/standalone/server.conf

# 3. Tirar o site da instância do sistema e recarregá-la (o vizinho segue no ar)
sudo rm /etc/nginx/sites-enabled/wikijuridica
sudo nginx -t && sudo systemctl reload nginx

# 4. Subir a dedicada
sudo ln -sf /opt/wiki/ops/systemd/wikijuridica-nginx.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now wikijuridica-nginx

# 5. Provar, não presumir
tools/check-static-freshness
tools/check-served-vs-manifest --amostra 60
tools/check-what-bots-see --rajada 10
```

**Reversão**, se qualquer passo reprovar:

```bash
sudo systemctl stop wikijuridica-nginx
sudo ln -sf /opt/wiki/ops/nginx/wikijuridica.conf /etc/nginx/sites-enabled/wikijuridica
sudo nginx -t && sudo systemctl reload nginx
```

## Manutenção enquanto as duas confs coexistem

`ops/nginx/wikijuridica.conf` (em uso) e `ops/nginx/standalone/server.conf`
(pronta) descrevem o mesmo `server {}`. Mudança em uma tem de ir para a outra —
até a troca acontecer e a primeira ser aposentada. A política de bots já está
num arquivo só (`standalone/bot-policy.conf`) justamente para reduzir essa
superfície de divergência.
