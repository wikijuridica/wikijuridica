# Agent Skills Discovery — o que o portal publica, e o que foi medido

**Norma:** `docs/rfc/agent-skills-discovery-v0.2.0.md` (cópia literal, commit
`1bd11679` de 2026-03-24, Apache-2.0) e a Agent Skills Specification
(`agentskills/agentskills`, `docs/specification.mdx` + `skills-ref/validator.py`,
lidos em 2026-08-20).

**Implementação:** `internal/agentskills` (núcleo, publisher e cliente) ·
`internal/httpserver/agentskills.go` (rotas) · `content/agent-skills/` (conteúdo) ·
`cmd/agent-skills` (CLI) · `cmd/generate-agent-skill-archives` (empacotador) ·
`internal/checks/agent_skills_discovery_gate.go` (gate).

---

## 1. Por que isto existe

A skill é o único artefato do ecossistema de descoberta que carrega **instrução
operacional**: não é catálogo de rotas nem descrição de API — é o manual que um agente
carrega no contexto e passa a seguir. O portal já publicava MCP, A2A, OpenAPI, ARD e
api-catalog; nenhum deles diz ao agente *como* usar o acervo.

Três fatos medidos em 2026-08-20 que definiram o desenho:

1. **Não existe implementação Go desta spec.** O único pacote Go do ecossistema
   (`niwoerner/go-agentskills`) tem 2 estrelas, está parado desde 2025-12-22 e não
   contém a string `well-known`. Não havia o que adotar.
2. **As implementações de referência da própria Cloudflare não cobrem `archive`.** Os
   quatro exemplos do repositório da spec declaram, literalmente, *"generates
   `type: "skill-md"` entries only"*.
3. **O consumidor real é `npx skills`** (`vercel-labs/skills`, 29.291 estrelas, MIT,
   v1.5.23 publicada em 2026-08-18). Ele escreve em `~/.agents/skills/`, que é
   exatamente onde Codex e OpenCode procuram. É a ponte entre o well-known e os
   clientes que não o consultam.

## 2. Conformidade — MUST por MUST, com o comando que prova

| # | Obrigação da spec | Onde | Evidência |
|---|---|---|---|
| P1 | índice em `/.well-known/agent-skills/index.json` | `httpserver.go` case do índice | `curl -sI .../index.json` |
| P2 | `$schema` exato | `agentskills.SchemaDiscoveryV020` | `TestAcervoRealEConformeAEspecificacao` |
| P3 | cinco campos por entrada | `agentskills.EntradaDeIndice` | idem |
| P4 | `type` ∈ {`skill-md`, `archive`} | tipo **derivado** do material presente | `TestTipoTemDeCasarComOMaterialDeApoio` |
| P5 | `digest` = SHA-256 dos bytes crus | `agentskills.DigestDe` | `TestDigestDoIndiceBateComOByteServido` |
| P6 | `name` 1–64, minúsculo, sem hífen na borda, sem `--` | `agentskills.validaNome` | `TestNomeReprovaCadaRegraDaSpec` |
| P7 | `description` ≤ 1024 | `agentskills.validaDescricao` | `TestDescricaoObrigatoriaEComTeto` |
| P8–P10 | `application/json` · `text/markdown` · `application/gzip` | `agentskills.MediaType*` | `TestServidorRespondeOsRequisitosHTTPDaSpec` |
| P11 | `GET` e `HEAD` | `http.ServeContent` | idem |
| P12 | `404` para inexistente | `respondeNaoEncontradoDeHabilidade` | `TestHabilidadeInexistenteResponde404EmJSON` |
| P13 | archive com `SKILL.md` na raiz, sem `..` | `agentskills.EmpacotaTarGz` | `TestArchiveNaoTemDiretorioInvolucro` |
| P14 | `Cache-Control` e CORS | `serveArtefatoDeHabilidade` | medido por `curl` |
| C1–C17 | os requisitos de cliente | `agentskills/cliente.go` | `cliente_test.go`, um caso por requisito |

Prova de ponta a ponta, contra a origem viva:

```
./tools/go-modern run ./cmd/check agent-skills-discovery
./tools/go-modern run ./cmd/agent-skills verify https://wikijuridica.com.br
```

O primeiro roda sobre o repositório e **não abre socket**. O segundo é o cliente
conforme, de fora. São instrumentos com alcances diferentes — a distinção existe porque
este projeto já produziu veredito causal falso usando uma sonda que só via `127.0.0.1`.

## 3. Decisões de arquitetura, com o motivo

**O conteúdo vive em `content/agent-skills/`, não em código.** Até 2026-08-20 as duas
habilidades publicadas eram string Go dentro de `agentskills.go` — e foi assim que uma
delas passou meses ensinando a rota `/consumidor/exemplo/`, que responde 404. Conteúdo
escondido em código não é revisado como conteúdo.

**Servido pelo binário, nunca materializado em `public/`.** O nginx resolve
`try_files $uri` **antes** do proxy: um arquivo homônimo em `public/` sombrearia a rota
em silêncio. `TestDescritoresNaoTemArquivoHomonimoEmPublic` deriva a lista de rotas do
acervo real, então habilidade nova herda a proibição sozinha.

**Os archives são commitados, não gerados no boot.** A saída do `compress/flate` não é
estável entre versões de Go. Montado em runtime, o digest mudaria num bump de toolchain
e — como a URL do artefato é imutável — todo cliente conforme passaria a **rejeitar** o
conteúdo, que é a única coisa que a spec proíbe terminantemente. O empacotador roda em
`tools/generate-agent-skill-archives`, o resultado é versionado, e o servidor só lê.

**URL derivada do digest, nunca contador manual.** `…/<nome>/<sha256[:12]>/SKILL.md`
muda quando, e somente quando, os bytes mudam. Um `/v1/`, `/v2/` mantido à mão se
desalinha do conteúdo — que é exatamente a falha que a URL versionada existiria para
resolver. O caminho convencional continua servindo, com `Content-Location` apontando a
versão imutável, porque é o caminho que os scanners de terceiro sondam.

**O manifesto registra dois níveis de digest.** O do archive e o de cada arquivo-fonte.
Sem o segundo, alguém edita `references/PROTOCOLO.md`, esquece de regerar, e o que é
servido passa a mentir sobre a fonte sem que nada acuse.

**Índice v0.1.0 em `/.well-known/skills/`.** Não é retrocompatibilidade decorativa: o
OpenCode é o único cliente que busca well-known nativamente, e o decodificador dele
exige `files` e não conhece `digest`. Servindo só o formato novo, o portal era invisível
para ele. O campo `version` é o **único** invalidador de cache dele — sem ele, quem
instalou fica preso àquela cópia para sempre.

**Não há caminho de execução no código.** A spec diz SHALL NOT executar `scripts/` por
padrão. A forma mais forte de cumprir é não existir `exec` no pacote: um portão que não
existe não pode ser afrouxado por engano.

## 4. Limites de extração, com a âncora de cada número

Constam de `internal/agentskills/desempacotador.go` e não são arbitrários:

| limite | valor | âncora |
|---|---|---|
| razão de compressão | 100:1 | teto real do DEFLATE **medido nesta máquina**: 1030:1 (100 MB de zeros → 101.797 bytes). Markdown real comprime 3–10:1 |
| total descomprimido | 32 MB | os maiores artefatos do portal têm ~1 KB; a spec recomenda nível 2 abaixo de 5k tokens |
| arquivos | 512 | a árvore-exemplo da spec tem 4; 512 barra o "tar bomb" de milhões de entradas vazias |
| profundidade | 8 | `scripts/`, `references/` e `assets/` são um nível |
| `index.json` | 1 MB | medido: 894 bytes |
| `SKILL.md` | 256 KB | medidos: ~1 KB |

Todo link (simbólico e físico) é recusado, não só o que escapa: é mais simples de
auditar, é o que o cliente de referência faz, e nenhuma skill legítima precisa de link.
O que conta para o limite é o que o `io.Copy` **escreveu** — o `Size` do cabeçalho é
escrito por quem monta o archive e pode mentir.

## 5. Registro de achados

Registro vivo em `.agents/runtime/agent-skills-goal/RA.jsonl`. Os que a implementação
desta frente fechou:

| ID | achado | como fechou |
|---|---|---|
| RA-001 | o `SKILL.md` no ar ensinava `/consumidor/exemplo/`, que responde 404 | conteúdo reescrito em `content/agent-skills/`, e um teste varre as rotas ensinadas |
| RA-002 | `description` do índice divergia do frontmatter (101 × 63 caracteres) | fonte única: o índice deriva do frontmatter parseado |
| RA-004 | 404 de habilidade respondia HTML de 7.361 bytes a cliente de máquina | 404 em JSON; o status já era certo pela RFC 8615 |
| RA-006 | `HEAD` sem `Content-Length`; `Range` devolvia 200 com o corpo inteiro | `http.ServeContent` |
| RA-012 | lista de artefatos aquecidos nomeava habilidade à mão | derivada de `cmd/agent-skills rotas`; 11 → 58 artefatos |
| RA-013 | a sonda aprovava índice vazio como "0 de 0 conferem" | piso explícito no gate |
| RA-014 | quatro gates estavam fora do ledger de performance desde que nasceram | ledger regenerado: 312 → 317 |
| RA-022 | `POST /mcp` sem `text/event-stream` no `Accept` responde 400 | documentado na skill e no script |

Achados de terceiros que esta frente **não** fecha, e por quê: RA-015 (borda servindo
CSP obsoleta — a purga-tudo de 08:53 UTC não fechou, causa não estabelecida), RA-021
(os `updated` do feed se agrupam em seis carimbos por publicação em lote, o que é a
task `conteudo-datas-recarimbo`), RA-007 e RA-005 (tocam `descritores.go`, o roteador do
api-catalog e `ops/nginx`, reivindicados por outra sessão no bus de coordenação).

## 6. O que a norma diz e o portal ainda não faz

- **O sufixo `agent-skills` não está registrado na IANA.** Consulta ao CSV oficial em
  2026-08-20: 115 sufixos, `agent-card.json` presente (permanente, Linux Foundation),
  `agent-skills` ausente. A RFC 8615 §3.1 põe a obrigação de registrar no autor da
  especificação, não em quem a implementa — mas o fato fica escrito aqui em vez de
  omitido.
- **O `$schema` não resolve.** `schemas.agentskills.io` responde NXDOMAIN. Isso está
  conforme (a spec diz que a URI é identificador opaco e "does not need to be
  resolvable"), e tem consequência de engenharia: **não existe JSON Schema oficial contra
  o qual validar**. Nossa validação é reimplementação das regras em prosa, e código que
  tentar buscar a URI falha em DNS, sempre.
- **`/.well-known/` e `/.well-known/agent-skills/` respondem 404, e está certo.** A
  RFC 8615 §3 diz que clientes não devem esperar recurso nesses caminhos. O que mudou é
  o corpo, que agora fala com máquina.
