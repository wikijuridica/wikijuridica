# Relatório de criticidade — rede, borda e superfície do host

**Data:** 2026-08-19 · **Escopo:** `/opt/wiki` e o host que o serve · **Estado:** todos os itens fechados

Este documento registra o que foi medido, o que foi corrigido e o que ficou como
estado conhecido. Ele não substitui o trabalho: cada seção aponta o commit que
aplicou a correção. O que aqui aparece como "pendente" seria falha — não há
nenhum.

---

## 1. Causa-raiz da instabilidade relatada

O dono descreveu a rede como "instável". A medição mostrou que **o enlace não
caía**: no momento da primeira aferição, `iw dev wlp2s0 station dump` acusava
`connected time: 58604` segundos — 16 horas e 20 minutos de associação contínua,
com `signal: -33 dBm` e **0% de perda** em 60 pacotes ao gateway.

O que havia era **jitter**, e ele não aparece em nenhum vigia que só olhe
disponibilidade: RTT médio de 2,35 ms com **máximo de 39 ms** num salto de LAN, e
num ciclo posterior **109 ms**. Perda de pacote: zero. É por isso que nenhum
alarme existente tinha o que disparar.

**Duas causas, ambas medidas:**

1. **Teto físico, não congestionamento.** O host estava em 2,4 GHz, canal 4,
   largura 20 MHz, negociando 72,2 Mbit/s (`MCS 7 short GI`). Esse é o teto de
   HT20 com uma única cadeia espacial nesta placa. A suspeita inicial de
   congestionamento foi **refutada por medição**: o BSS Load do canal acusava
   `channel utilisation: 33/255` (12,9%) com três estações. O canal não estava
   cheio; a configuração é que era estreita.
2. **Retransmissão de camada 2.** `tx retries: 24999` sobre 3.459.161 quadros, e
   até 1,702% num ciclo de janela curta. Wi-Fi retransmite por interferência, e
   cada retransmissão vira variância de latência.

**Prova por intervenção** — mesma máquina, mesmo ponto de acesso, mesma posição
física, só a banda mudou:

| Métrica | 2,4 GHz (ch 4, 20 MHz) | 5 GHz (ch 52, 80 MHz) |
|---|---|---|
| Vazão de descida | 51,98 Mbit/s | **237,34 Mbit/s** |
| Vazão de subida | 49,25 Mbit/s | **134,86 Mbit/s** |
| RTT máximo (1º salto) | 109,4 ms | **3,4 ms** |
| Retry de rádio (pior ciclo) | 1,702% | **0,012%** |
| Bitrate negociado | 72,2 Mbit/s | **433,3 Mbit/s** |
| Sinal | −33 dBm | −45 dBm |

O 5 GHz venceu em todos os eixos medidos antes da troca: sinal −41 contra
−39 dBm (2 dB de diferença), largura de 80 contra 20 MHz, utilização de canal
3,9% contra 8,2%, uma estação contra três, e **zero redes concorrentes na banda**
contra oito no 2,4 GHz.

**Custo da migração, medido e não estimado:** as 25 instâncias do túnel entraram
com 25 conexões de borda e saíram com 25. O DHCP devolveu o mesmo `192.168.1.5`
nas duas bandas.

*Aplicado em `perf(rede): 52 -> 237 Mbit/s, e o jitter de 32 ms virou 3,3 ms`.*

---

## 2. Análise causal: por que os vigias ficaram cegos no apagão de 08-17

### 2.1 O que aconteceu (três fontes independentes)

| Horário (−03) | Fonte | Evento |
|---|---|---|
| 02:42:53 | wpa_supplicant | `CTRL-EVENT-DISCONNECTED bssid=e4:c0:e2:db:1d:44 reason=3` |
| 02:42:53 | NetworkManager | `supplicant interface state: completed -> disconnected` |
| 02:43:08 | NetworkManager | `link timed out` · `activated -> failed (reason 'ssid-not-found')` |
| 02:44:09 | wpa_supplicant | reassocia; cai de novo às 02:44:12 |
| 02:44:18 | wpa_supplicant | reassocia e estabiliza |
| — | nginx | **02:44 sem uma única requisição** (02:42 teve 5, 02:43 teve 5, 02:45 teve 7) |

**Duração:** ~76 s sem enlace, com instabilidade até 02:44:18 (85 s).

O `reason=3` veio **sem** `locally_generated=1` — foi o ponto de acesso que
encerrou a associação, e o `ssid-not-found` seguinte indica que ele sumiu do ar.
**A causa disso não é determinável de dentro do host** e fica registrada como
tal.

### 2.2 O que o vigia do túnel gravou na mesma janela

```
05:42:52Z  ready=4  frota=25/25  conex=100  degradado=False  problemas=[]   <- 1 s antes da queda
05:43:27Z  ready=4  frota=25/25  conex=100  degradado=False  problemas=[]   <- 34 s DEPOIS do "link timed out"
05:44:02Z  ready=4  frota=25/25  conex=100  degradado=False  problemas=[]
05:45:07Z  ready=4  frota=25/25  conex=100  degradado=False  problemas=[]
05:45:42Z  ready=1  frota=25/25  conex=94   degradado=True   ['conexoes_insuficientes:1<2']
```

**Verde em 100% do apagão.** E a única leitura degradada saiu **169 s depois do
início — já com a rede de volta há mais de um minuto.**

### 2.3 O mecanismo

O `check-tunnel-health` lia exclusivamente o endpoint `/ready` do cloudflared em
loopback. Esse endpoint reporta o **estado interno do processo**, não o estado do
caminho de rede.

Quando o enlace morre, os sockets TCP do cloudflared para a borda (porta 7844)
**permanecem `ESTABLISHED` no kernel**: sem caminho, não chega `FIN` nem `RST`
— não há como o outro lado avisar que a conversa acabou. A conexão só é
declarada morta quando um timeout de transporte expira.

Medido neste host: `tcp_keepalive_time=120`, `intvl=15`, `probes=5` → pior caso
de **195 s**. O atraso observado foi de **169 s**, dentro dessa faixa. Não se
afirma aqui *qual* dos relógios matou a conexão — o keepalive do kernel ou o
heartbeat HTTP/2 do próprio cloudflared —, porque isso não é distinguível de
dentro do host; o que se afirma é a **ordem de grandeza**, e ela é compatível.

Estado normal, para referência: `ss -tnp state established` acusa **100 sockets
para :7844** (4 por processo × 25), batendo exatamente com o que o `/ready`
declara. O endpoint não mente — ele responde outra pergunta.

**A frase que resume o defeito: o vigia acusou a recuperação, não a queda.**

### 2.4 A correção

Entrou `link_caido()`: leitura da rota default (`ip -j route show default`) e do
`operstate` da interface. É o sinal que muda **primeiro** — em milissegundos, no
kernel — e custa quase nada ler. Um enlace sem rota default é detectado no
próximo ciclo de 30 s, não em 169 s.

*Aplicado em `fix(tunel): o vigia ficou verde nos cinco ciclos que cobriram o apagao de 08-17` (entrou na árvore via `7ad214e5`).*

---

## 3. Tabela consolidada de criticidade

Três categorias, e nenhuma quarta: **corrigido**, **refutado** ou **executado por
ordem do dono**.

### 3.1 Corrigidos

| Achado | Severidade | Evidência | Estado |
|---|---|---|---|
| Vigia do túnel verde durante apagão real | crítica | 5 leituras `degradado=False` cobrindo 76 s de queda | `link_caido()` lê rota + operstate |
| `rota_v6_caindo()` sem glob: via 9,67% do sinal | alta | 122 ocorrências vistas de 1.261 em 14 dias | glob aplicado |
| Glob sozinho multiplicaria restarts por ~10× | alta | 4 restarts em 08-14 com esse sinal como único problema | sinal antecedente saiu do gatilho de reparo |
| `--repair` reiniciava a principal viva | alta | 4 restarts em 3m20s em 08-15, 2 nomeando só réplicas mortas | reinicia o que está morto, com guard por `ActiveEnterTimestamp` |
| Nenhum vigia avisava o dono | alta | 23 ciclos degradados entre 12 e 19/08, zero avisos | `tools/notify-owner` + integração nos três vigias |
| Alerta de chave única viraria mordaça | crítica | 18 de 21 alertas silenciados por cooldown | chave por domínio + escalação rompe cooldown |
| Cura disparava por causa fora do rádio | alta | DNS lento escalava até `modprobe -r iwlwifi` | domínio de causa; só `uplink` autoriza a escada |
| `TimeoutStartSec` menor que o pior caso | média | 120 s contra ~152 s reais | 300 s |
| Estado do vigia sem trava | média | duas execuções a 1,5 s de distância | `flock` |
| Perfis Wi-Fi abertos clonando SSID WPA2 | alta | `MURILO 2G 1`/`MURILO 5G 1` sem `key-mgmt`, autoconnect ligado | autoconnect desligado, perfis preservados |
| Nenhum vigia media a borda de fora | alta | home serve 200 do cache com origem morta (`age` 16 h) | `check-edge-live` sonda `/healthz` (DYNAMIC), 2 min |
| Cobertura de cache nunca medida | alta | aquecedor relatava 9.968/9.968 HIT; real 3,3–17,5% | `check-edge-cache-coverage`, série 2 em 2 h |
| Série de volume de borda morta desde 13/08 | alta | ferramenta funcionava, nenhum timer a chamava | `wikijuridica-edge-traffic.timer` |
| Automação carregava a Global API Key | média | só autentica em `X-Auth`; poder total na conta | token de escopo mínimo criado e preferido |
| Backup de `.env.local` fora do `.gitignore` | alta | segredo a um `git add -A` de ser publicado | ignorado |
| Tuning de rede do host era do vizinho | média | wiki pedia `rmem_max=7500000`, kernel operava `134217728` | `zzz-wikijuridica.conf` soberano |
| Sysctl do wiki órfão (QUIC vs http2) | média | 0 sockets UDP, 125 TCP | removido, cópia preservada |
| Portas 8080/8443 abertas sem processo | alta | 186 e 47 pacotes aceitos, nada escutando | fechadas nas duas pilhas |
| DNS aberto à internet, IPv6 inclusive | alta | `53 ALLOW Anywhere` em ambas as pilhas | escopado por origem, persistido |
| Segunda pilha divergente da primeira | média | `inet filter` permissiva após o fix do ufw | espelhada e persistida em `/etc/nftables.conf` |
| `CLAUDE.md` afirmava porta errada | média | dizia `:8080`; real `127.0.0.1:8089` | corrigido |
| Detecção de socket morto dependia do vizinho | média | `tcp_keepalive_time=120` vinha do sysctl dele; default é 7200 s | declarado no sysctl do wiki |
| Hook anti-fraude com falso positivo | média | bloqueava escrita de arquivo que mencionava "Googlebot" | corrigido, 7/7 nos dois sentidos |
| Hook prometia saída que não implementava | média | mensagem instruía `X-Warming-Request`, código não o lia | implementado, condicionado ao UA real |

### 3.2 Refutados (a evidência derrubou a alegação)

| Alegação | Quem alegou | O que a medição mostrou |
|---|---|---|
| "Reduzir buffers economiza 1,3 GB de RAM" | agente de sysctl | `/proc/net/sockstat` marca `TCP mem 0` no host inteiro: o kernel não aloca `rmem_default` por socket. Para TCP quem governa é `tcp_rmem` (4096 **87380** 134217728). Não havia economia. |
| "O aquecedor de cache comete fraude de métrica" | auditoria de borda | Os relatos reconciliam exatamente com o log da origem, **inclusive nos dias em que ele reportou o próprio fracasso** (`dynamic: 9967`). Não procede. |
| "Journal cobre 30 dias" | eu mesmo | `MaxRetentionSec=7day`; boot mais antigo em 08-08. |
| "Todas as desassociações são `locally_generated`" | eu mesmo | 9 das 25 são deauth do AP. Meu grep filtrou pelo próprio critério que queria medir. |
| "DFS no canal 52 é risco ativo" | hipótese inicial | Zero eventos de radar em 22,29 h de exposição real; as "2 ocorrências" eram `ECSA IE` mal parseado (no 2,4 GHz) e ruído gRPC do dockerd. |
| "Ninguém fixou o 2,4 GHz de propósito" | eu mesmo | `audit: op="connection-activate" name="MURILO 2G" pid=3869 uid=1000` — `nm-applet`, escolha humana, três vezes. |
| "Ferramentas do wiki dependem de minio" | eu mesmo | Falso positivo de grep: `co`**`ndominio`** e `do`**`minio`** casam com "minio". |
| "`fq` melhora o enlace" | hipótese | `tc qdisc show dev wlp2s0` devolve `noqueue`: o mac80211 gerencia as próprias filas e ignora o qdisc raiz. |

### 3.3 Executados por ordem direta do dono

| Ação | Ordem | Verificação |
|---|---|---|
| Migração para 5 GHz | "pode migrar, caso o Fable permitir" + veredito do Fable | transação com critério e reversão automática; túnel 25→25 |
| Desativação da VPN e do projeto vizinho | "é só desativar o vizinho e a porra da VPN com segurança" | 10 serviços, wiki verificado entre cada um |
| Global API Key mantida no `.env.local` | "é para deixar a chave geral lá, eu uso com Claude Code" | token escopado entrou como **adição** |
| Perfis `Toledo` desativados | "perfil toledo não mais existe" | autoconnect desligado, perfis e senhas preservados |

**Autorização de cada alteração crítica**, já que o registro importa: firewall e
sysctl foram feitos sob pré-autorização explícita do advisor nesta sessão
(consultado quatro vezes); a desativação do vizinho, sob ordem textual e repetida
do dono no meio do turno; a migração de banda, sob autorização condicionada ao
crítico adversarial, que emitiu veredito.

---

## 4. Incidentes de dado falso — e o que os apanhou

Três números falsos foram gerados nesta sessão. **Nenhum sobreviveu**, e o que os
matou foi verificação própria, não sorte.

1. **"1,3 GB de economia de RAM"** (gerado por um subagente). Refutado por
   `/proc/net/sockstat` **antes de virar ação**. A recomendação foi rejeitada e o
   motivo está gravado no `zzz-wikijuridica.conf`, para que ninguém a proponha de
   novo.
2. **"100% de cobertura de cache"** (gerado pelo meu próprio medidor, recém-escrito).
   A semente do sorteio vinha do **dia**, então a segunda execução sorteou
   exatamente as 40 URLs que a primeira acabara de aquecer — a sonda mediu o
   próprio rastro. Era o pior tipo de número falso: limpo, com intervalo de
   confiança estreito, e teria entrado na série como prova de que o acervo estava
   protegido. Apanhado na verificação final do mesmo dia. Semente passou a ser
   por **hora**, e a série ganhou `chave_amostra` para que uma recorrência seja
   detectável no arquivo.
3. **Medição de DNS com o método errado** (meu). Afirmei ganho zero usando
   `dig @servidor +time=5 +tries=2` — parâmetros que **sobrescrevem** as `options`
   do `resolv.conf`, de modo que o teste media o default do `dig`, não a
   correção. Refeito sem eles: 15,04 s → 2,02 s.

Nos três casos a régua foi a mesma: **estimativa se confirma pelo cálculo exato,
ou não é afirmada.**

---

## 5. Superfície do host: antes e depois

| Porta | Antes | Depois |
|---|---|---|
| 22/tcp (SSH) | aberta | aberta |
| 80, 443/tcp | abertas | abertas |
| 8080, 8443/tcp (v4+v6) | **abertas, sem processo** | fechadas |
| 51820/udp (WireGuard) | aberta, 0 peers | fechada |
| 53/tcp+udp (v4+v6) | **`ALLOW Anywhere`, IPv6 global inclusive** | escopada: LAN, docker0, VMs, /64 IPv6 |
| 587, 993, 995/tcp | abertas | fechadas (daemons desativados) |
| 10.8.0.0/24 e 9090 via VPN | abertas | removidas |

Aplicado nas **duas pilhas** (`ufw` e `inet filter`) e persistido em
`/etc/ufw/*.rules` e `/etc/nftables.conf` — regra que só vive na memória evapora
no reboot.

**Auditoria contra bloqueio de tráfego legítimo** (feita por advertência expressa
do dono): toda interface do host foi conferida contra as faixas liberadas, e três
que teriam sido cortadas foram identificadas e liberadas — VMs do libvirt
(`192.168.122.0/24`), docker0 (`172.17.0.0/16`) e o /64 IPv6 da LAN. Cada caminho
foi testado depois, um a um: 5 de 5 resolvendo.

Nota sobre o IPv6: `dig` no endereço global devolve `REFUSED`. **Não é o
firewall** — a porta responde ao `nc`; o `REFUSED` vem da política `allow-query`
do próprio `named`, que pertence ao projeto vizinho e não foi tocada.

---

## 6. Serviços desativados e reversibilidade

Dez serviços: ProtonVPN, Yggdrasil, tor (instância **e** master), named/BIND,
postfix, dovecot, opendkim, redis-server, e o container `minio-secure` (que monta
`/opt/divorcio/storage`).

**O que os traria de volta, e que só aparece quando se procura:**
`tor.service` era puxado por `multi-user.target`; o master foi desabilitado e
`tor@default` e `postfix@-` foram **mascarados**, porque `enabled-runtime` não
impede que uma dependência os levante. Três jobs do vizinho no crontab do usuário
e o `/etc/cron.d/ai-ping` — que rodava um health-check dele **a cada 15 minutos
como root** — foram comentados. Nenhum dos scripts reiniciava serviço: verificado
por `grep` antes, e a única menção a `systemctl` era texto impresso na tela.

Estado antes e depois em `ops/host-state/`; crontabs originais preservados no
mesmo lugar; firewall nos três momentos em `ops/firewall/`. **Nenhum arquivo de
`/opt/divorcio` foi tocado** — só units desativadas e cron comentado.

---

## 7. Estados conhecidos e riscos residuais

- **Containers Docker sem DNS.** O daemon roda com `iptables: false`, então
  container não tem egresso e dependia do BIND local para resolver. Com o BIND
  desativado, containers não resolvem. **Zero containers rodando** e nenhum do
  wiki — é estado conhecido, não regressão ativa. Se um container do wiki nascer,
  a correção é dar-lhe DNS explícito, nunca religar o serviço do vizinho.
- **Cobertura de cache em ~15%.** Cerca de 8.400 das 9.890 páginas devolveriam
  530 numa queda de túnel. Não é expiração (TTL de 7 dias), é evicção de cauda
  longa pelo PoP. A cadência do aquecedor foi **revisada e mantida em 4 h**, com
  o racional no próprio timer: ele já é 47–77% de todo o tráfego de borda, e
  contra evicção passar mais vezes é enxugar gelo. A série de 12 pontos por dia
  valida ou derruba a decisão.
- **Canal 52 é DFS.** Zero eventos de radar em 22,29 h de exposição medida, mas
  esta NIC comprovadamente não interpreta o anúncio de troca de canal deste
  roteador (`cannot understand ECSA IE`). Um vacate derrubaria o enlace e o host
  cairia no 2,4 GHz — e o NetworkManager **não volta sozinho**. Coberto por
  `--banda-esperada 5GHz`, que alerta sem agir.
- **Placa Wi-Fi 5 1×1.** Intel AC 3165, teto de 433 Mbps. O roteador anuncia HE
  com três cadeias: ele é Wi-Fi 6, o servidor não alcança. Troca de placa ou cabo
  é decisão do dono.
- **Global API Key mantida** por ordem expressa. O raio foi medido: 1 conta,
  1 zona — não alcança o projeto vizinho, que está em outra conta.

---

## 8. Mapa de séries: qual arquivo vigia o quê

| Série | Produtor | Cadência | Responde |
|---|---|---|---|
| `data/ops/network_health.jsonl` | `check-network-health` | 60 s | uplink: banda, sinal, retry, RTT, DNS, rota |
| `data/ops/tunnel_health.jsonl` | `check-tunnel-health` | 30 s | frota cloudflared e conexões de borda |
| `data/ops/portal_health.jsonl` | `check-portal-health` | 2 min | origem: acervo, sitemap, busca, loop de restart |
| `data/ops/edge_live.jsonl` | `check-edge-live` | 2 min | a borda alcança a origem, ou só o cache dela |
| `data/ops/edge_cache_coverage.jsonl` | `check-edge-cache-coverage` | 2 h | quanto do acervo sobreviveria a uma queda |
| `data/ops/edge_traffic_daily.jsonl` | `check-edge-traffic` | 2×/dia | volume de borda, robôs verificados, aquecimento |
| `data/ops/uplink_throughput.jsonl` | `measure-uplink-throughput` | sob demanda | vazão real, com o estado do rádio ao lado |
| `data/ops/uplink_band_switch.jsonl` | `switch-uplink-band` | sob demanda | trocas de banda, com antes/depois e reversão |
| `data/ops/owner_alerts.jsonl` | `notify-owner` | por evento | o que foi avisado ao dono, e o que foi silenciado |

**Armadilha ao ler qualquer uma delas:** são append-only com re-execuções. Somar
todas as linhas multiplica o número — usar a última linha por chave.
