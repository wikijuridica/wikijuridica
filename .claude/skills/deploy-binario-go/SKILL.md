---
name: deploy-binario-go
description: Use ao subir binário Go novo em produção (cmd/server) — a ordem dos passos é o produto, e invertê-la já causou 504 e uma hora de conteúdo antigo.
---

# Deploy de binário Go

```
./tools/deploy-binario-go
```

**O produto desta ferramenta é a ORDEM.** Não reproduza os passos à mão: em
2026-09-05 uma troca manual custou uma hora, com cinco tentativas seguidas
servindo o conteúdo **antigo**.

## Por que cada passo existe

1. **Build para nome temporário** — compilar por cima do binário em execução
   devolve `ETXTBSY` ("Text file busy"); já abortou um deploy em 2026-08-06.
2. **Validação ISOLADA** — porta própria **e** `WIKI_CACHE_DIR`/`WIKI_ACCESS_LOG_DIR`
   próprios. **Porta diferente não isola disco:** em 2026-08-19 uma segunda
   instância no mesmo `var/on-demand-cache` destruiu o índice de busca em
   produção — a busca respondia 200 com "Nenhum resultado" e nenhum health check
   viu. O log de acesso próprio é anti-fraude: sonda de validação com
   `warming=false` entraria no ledger que decide SEO como visita autêntica.
3. **Troca ATÔMICA (`os.replace`)** — `rename` troca o inode; `cp` por cima é
   não-atômico e reencontra o `ETXTBSY`.
4. **Socket ANTES do serviço** — socket `Type=notify` reativado com binário que
   ignora `LISTEN_FDS` faz bind próprio, toma `EADDRINUSE` e entra em laço de
   5 s com a porta em `LISTEN`: **504** para o visitante. Foram **1.435 respostas
   502** em 26–28/08/2026 até a fila existir. O socket não se para aqui: fica em
   `LISTEN` enfileirando (`FlushPending=no`), e o restart vira latência, não erro.
5. **Readiness PROVADA** — no Go (`127.0.0.1:8089`) **e pelo nginx**
   (`127.0.0.1:8088`). Houve 13 min em que o Go respondia e o proxy não.
6. **Invalidar origem, depois purgar borda** — a ordem inversa repopula o Tiered
   Cache com o conteúdo velho (skill `purgar-e-aquecer-borda`).

## Antes

Worktree compartilhada: o deploy compila `./cmd/...` **do worktree**. Arquivo em
edição de outra frente entra no binário. `git status` antes, sempre.

Mudou `content/social_policy.json`? O campo novo só entra no disco **junto** com
o swap do binário — senão o próximo restart vira laço de boot
(`Restart=always` + `log.Fatalf`).
