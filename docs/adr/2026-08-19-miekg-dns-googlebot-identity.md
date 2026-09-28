# ADR 2026-08-19: miekg/dns para verificação reversa-direta de identidade do Googlebot

Status: ADR **retroativo**. A dependência entrou em `go.mod` no commit `bfef1e55` (2026-07-03, "Integrate P0 operational evidence gates") sem ADR; este documento registra o estado medido em 2026-08-19 — inclusive o fato de que o verificador implementado **nunca é chamado fora de teste**.

## Contexto

Confiar em User-Agent para identificar o Googlebot é falha de segurança conhecida: qualquer cliente envia a string do Googlebot no cabeçalho. O procedimento oficial do Google (https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests) exige verificação em duas etapas: DNS reverso do IP de origem retornando um PTR sob domínio do Google, e DNS direto desse nome retornando de volta o mesmo IP. O resolver padrão da stdlib (`net.LookupAddr`) não permite fixar servidor nem timeout por consulta, nem inspecionar o RCODE da resposta — daí a necessidade de um cliente DNS de baixo nível.

O par dessa verificação é `github.com/gaissmai/bart` (`v0.28.0`), que faz o casamento de faixas CIDR publicadas pelo Google; os dois convivem em `internal/crawleridentity`. O BART responde "o IP está numa faixa oficial"; o DNS responde "o IP é realmente do Google".

## Versão fixada e licença

- Módulo: `github.com/miekg/dns`, versão **`v1.1.72`**, fixada em `go.mod` linha 29.
- Licença: **BSD-3-Clause**, lida em `~/go/pkg/mod/github.com/miekg/dns@v1.1.72/LICENSE` ("BSD 3-Clause License / Copyright (c) 2009, The Go Authors. Extensions copyright (c) 2011, Miek Gieben.").
- A versão e a licença estão também declaradas como constantes no código, em `internal/crawleridentity/identity.go:29-31` (`DNSModulePath`, `DNSModuleVersion`, `DNSModuleLicense`), e batem com o disco.

## Onde é usada de fato

Import de produção único: `internal/crawleridentity/identity.go:19` (`miekgdns "github.com/miekg/dns"`). Há um segundo import, de teste, em `internal/crawleridentity/identity_test.go:12`.

O uso real está concentrado no tipo `MiekgDNSResolver` (`identity.go:130`), que implementa a interface `DNSResolver` (`identity.go:125`):

- `identity.go:402` — `miekgdns.ReverseAddr(ip.String())` monta o nome `in-addr.arpa`/`ip6.arpa`.
- `identity.go:406-416` — consulta PTR, extrai `*miekgdns.PTR` e normaliza com `miekgdns.Fqdn`.
- `identity.go:427-438` — consulta A e AAAA para o nome do PTR (a etapa "direta").
- `identity.go:448-467` — `exchange`: monta `miekgdns.Msg`, aplica `Timeout`, exige `RcodeSuccess`.
- `identity.go:497` — grava o PTR aceito na verificação.

A implementação é correta e completa. O problema está no próximo item.

## Runtime de produção: NÃO — linkada, nunca invocada

Duas medições, ambas reproduzíveis por grep:

**(a) O tipo nunca é instanciado fora de teste.** `grep -rn 'MiekgDNSResolver' --include=*.go internal/ cmd/ | grep -v _test.go` retorna **apenas as quatro linhas da própria definição** (`identity.go:130`, `398`, `421`, `448`). Nenhum código de produção constrói um `MiekgDNSResolver`, e portanto nenhuma consulta DNS real é feita por este projeto.

**(b) O gerador da evidência não recebe resolver.** `crawleridentity.BuildEvidenceRecord(checkedAt, payload)` (`identity.go:227`) tem dois parâmetros e nenhum deles é um `DNSResolver`; `cmd/generate-crawler-identity-bart/main.go` chama exatamente essa assinatura. O que esse comando busca na rede é o JSON de faixas de IP do Google, por HTTPS — não DNS.

O que o caminho de release realmente consome de `internal/crawleridentity` são funções que **leem a evidência já gravada**: `LoadVerifiedIdentity` (`internal/crawlsmoke/smoke.go:156`, `internal/publicrelease/publicrelease.go:3054`) e a constante `GooglebotUserAgent` (`smoke.go:453`, `publicrelease.go:3563`) — isto é, o smoke usa justamente o User-Agent, que a própria política do adapter declara ser "smoke signal" e não identidade verificada.

Alcance por grafo estático de imports: `cmd/server`, `cmd/build` e `cmd/publish-v2-direct` **não alcançam** `miekg/dns`. Alcançam 38 entrypoints, entre eles `cmd/promote-authorial-mass-public-release`, `cmd/rollback-authorial-mass-public-release`, `cmd/snapshot-public-release` e `cmd/check` — ou seja, o módulo é **linkado nos binários de promoção pública**, mas o código que ele fornece não roda. (Contagem por grafo de imports; `//go:build` não avaliado, então 38 é limite superior — `cmd/generate-crawler-identity-bart`, por exemplo, é `//go:build devcmds`.)

## Benchmark 10k/100k: não aplicável, e não realizado

Não há throughput a medir: a dependência não processa registros. O que existiria para medir seria latência de verificação por requisição — e não há verificação acontecendo.

`data/ops/crawler_identity_bart_evidence.jsonl` contém dados reais **da parte BART**: `prefix_count: 315`, `ipv4_prefix_count: 169`, `ipv6_prefix_count: 146`, `official_payload_sha256`, `official_payload_creation_time: 2026-06-29T14:45:47`, com `sample_matched: true` e `sample_miss_matched: false` — isso é casamento de CIDR de verdade, feito pelo `bart`.

Os campos de DNS do mesmo registro **não são medição**:

- `sample_dns_ptr_name` é construído por concatenação de string em `identity.go:260`: `"crawl-" + strings.ReplaceAll(sampleIP.String(), ".", "-") + ".googlebot.com."`. É por isso que o valor gravado é o literal malformado `"crawl-2001:4860:4801:10::.googlebot.com."` — um endereço IPv6 passado por um substituidor de pontos, que nenhum PTR real do Google devolveria.
- `sample_dns_forward_matched: true` é literal em `identity.go:261`.

E o validador `identity.go:562` exige exatamente esses dois campos para aprovar o registro — o gate valida um valor que o próprio gerador fabricou. Isso é falso verde por construção.

## Alternativas consideradas

Decisão histórica **não documentada na época**; este ADR é retroativo. O registro contemporâneo mais próximo é `internal/ossinstallmatrix/matrix.go:522-535`, que declara `BenchmarkPlan: "PTR plus forward DNS verification for Googlebot identity without user-agent-only trust or publication writes"` e `AdapterPlan: "blocked crawleridentity DNS verifier using miekg/dns with local-testable resolver contract"`. A intenção registrada é exatamente a verificação em duas etapas — a implementação foi entregue e a ligação com o caminho de execução, não.

Alternativa óbvia e não registrada: `net.LookupAddr`/`net.LookupIP` da stdlib, que fariam reverso e direto sem dependência externa, ao custo de perder controle de servidor, timeout por consulta e inspeção de RCODE — os três recursos que `MiekgDNSResolver` de fato usa (`identity.go:448-467`). A escolha é defensável; simplesmente não foi escrita. Não há `Record` de dependência para `miekg/dns` em `internal/codex2policyenforcement/policy.go` (busca por `miekg/dns` no arquivo: zero ocorrências).

## Risco e saída

Licença BSD-3-Clause, permissiva; `miekg/dns` é a biblioteca DNS de referência do ecossistema Go, madura e amplamente auditada. Risco de licença e de manutenção: baixo.

O risco relevante aqui não é a dependência — é a **lacuna que ela mascara**. Enquanto o resolver não for ligado, o portal não tem verificação real de identidade de crawler, e a evidência que existe sugere o contrário. Isso importa diretamente para o objetivo do projeto: distinguir Googlebot verdadeiro de falsificado é o que separa métrica de rastreio real de métrica contaminada.

Se a dependência sumisse: nenhum binário de produção perde comportamento, porque nenhum comportamento dela é executado. Quebraria a compilação de `internal/crawleridentity` e dos 38 binários que o linkam, e o gate `check-crawler-identity-bart` reprovaria. A saída técnica é curta — trocar `MiekgDNSResolver` por um resolver de stdlib atrás da mesma interface `DNSResolver` (`identity.go:125`), que existe justamente para isso.

## Consequências e pendência registrada

O registro documental exigido pelo contrato passa a existir. Fica registrado como defeito a corrigir em sessão dedicada, com causa nomeada: `internal/crawleridentity/identity.go:260-261` grava `sample_dns_ptr_name` sintetizado por concatenação e `sample_dns_forward_matched: true` fixo, sem que consulta DNS alguma tenha sido feita, e `identity.go:562` valida esses mesmos campos. A correção correta é ligar `MiekgDNSResolver` (ou um resolver injetado) ao gerador de evidência, de modo que os campos passem a refletir consulta real — ou, se a consulta não puder ocorrer no ambiente do gate, emitir os campos como não verificados em vez de verdadeiros.

## Adendo 2026-08-19 (mesma data, após a correção): pendência fechada

O corpo acima descreve o estado **medido antes** da correção e fica como registro histórico. O defeito nomeado na seção anterior foi corrigido na mesma data, em `internal/crawleridentity`:

- Os dois campos fabricados deixaram de existir. `sample_dns_ptr_name` e `sample_dns_forward_matched` foram substituídos por campos que declaram **política** — `policy_requires_forward_dns_match` e `policy_accepted_ptr_suffixes` (este lido de `AllowedGoogleCrawlerPTRSuffixes`, a mesma lista que `allowedGoogleCrawlerPTR` usa, o que torna o campo coerência de configuração conferível).
- O **resultado real** passou a ter lugar próprio e opcional: `sample_dns_verification`. Ausente = nenhuma consulta foi feita e nada é afirmado. Presente = afirmação de execução, conferida campo a campo pelo validador (PTR aceito tem de constar entre os PTR observados; IP direto confirmado tem de constar entre os IPs observados; `verified_googlebot` só vale com as duas etapas sustentadas). Registro que declare verificação sem tê-la executado **reprova**.
- `MiekgDNSResolver` passou a ser instanciado fora de teste: `crawleridentity.AttachSampleDNSVerification` é chamado por `cmd/generate-crawler-identity-bart` quando `-dns-server` é informado. `LookupPTR` passou a tratar NXDOMAIN como resposta ("sem PTR"), não como falha de consulta.
- A evidência foi regerada pelo gerador sancionado com consulta DNS real (`-dns-server 192.168.1.1`). O PTR verdadeiro de `2001:4860:4801:10::` é `crawl-2001-4860-4801-0010-0000-0000-0000-0000.googlebot.com.`, e o AAAA desse nome devolve o mesmo endereço — reverso e direto fecham de verdade. Confere-se por `dig -x 2001:4860:4801:10::`. Compare com o literal fabricado que estava gravado até então, `crawl-2001:4860:4801:10::.googlebot.com.`, que nenhum resolver devolveria.
