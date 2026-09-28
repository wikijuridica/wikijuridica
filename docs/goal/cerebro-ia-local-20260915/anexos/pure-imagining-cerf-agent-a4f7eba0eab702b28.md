# REDE SOCIAL DE IA — ÂNGULO DADO E PROTOCOLO

**Como um agente participa.** Plano de arquitetura e implementação, 2026-09-15.
Sessão em PLAN MODE: tudo abaixo foi **lido e medido**, nada foi escrito no repositório.

---

## TESE

A rede social de IA não se constrói: ela se **liga e se preenche**. Os quatro pilares do
ângulo dado-e-protocolo já existem no disco e nunca foram conectados entre si:
identidade de agente (`internal/oauthserver`, escopo único `relatos:escrever`), escrita de
agente com cota e proveniência verificada (`internal/agentreports`), escrita do cérebro sob
assinatura do advogado (`cmd/social/interno.go`, socket + HMAC + ledger idempotente) e o
objeto citável de thread (`internal/socialrender/duvida.go` → HTML, gêmea, exportação, Atom,
MCP, os cinco de uma struct só).

O que **não existe** é o elemento distintivo: a **refutação** — um objeto que aponta para
uma alegação nominada dentro de um texto publicado e traz evidência com proveniência. E o
que **falta ligar** é a citabilidade: medi agora que `/api/v1/citar` responde 200 em
1.786 bytes para a página do acervo e **404 `page_not_published`** para qualquer rota da
rede social. Uma discussão que um LLM não pode citar com a mesma segurança com que cita uma
lei é uma discussão que ele lê e descarta.

---

## 0. AS MEDIÇÕES DESTA FRENTE (lidas nesta sessão, não herdadas do dossiê)

| # | O que medi | Resultado | Camada | Como |
|---|---|---|---|---|
| M1 | `/api/v1/citar` cobre a rede social? | **Não: 404 `page_not_published`.** Controle positivo: `/api/v1/citar/autonomos/b2b-escopo-alterado/` = **200, 1.786 B, 15 campos** (`html_sha256`, `markdown_sha256`, `referencia_abnt`, `sources`, `oab`, `verificacao`…) | origem (127.0.0.1:8088) | `curl` com UA do projeto + `X-Warming-Request: true`; path real tirado de `published_manifest.jsonl` |
| M2 | Custo unitário de servir um agente na rede social — **o dossiê marcou como nunca agregado** | `tema_html` n=8.363 **p50 3 ms, p90 4, p99 6, max 28**; `gemea_md` n=1.213 p50 3, p99 5; `atom` n=1.093 p50 2, p99 6; `outro` n=170 p50 6, p99 11. **Dia inteiro = 33,2 s de handler.** 10.839 linhas com `duration_ms` | origem (nginx, travessia 98,7% nesta superfície) | agregação de `duration_ms` em `data/ops/access/nginx-2026-09-15.jsonl`, filtro `path.startswith('/redesocial/')` |
| M3 | `contas` aceita um agente hoje? | **Não.** `email_indice TEXT NOT NULL UNIQUE`, `email_cifrado BLOB NOT NULL`, `senha_phc TEXT NOT NULL`, `CHECK (papel IN ('leigo','advogado','jurista'))` | disco | `internal/contas/schema.sql:38-53` |
| M4 | Raio de explosão de uma migração de `contas` | **8 arquivos não-teste**, todos em `internal/contas/` exceto `internal/lgpd/art18.go` | disco | `grep -rn "email_indice\|email_cifrado\|senha_phc" --include=*.go internal/ cmd/` |
| M5 | A purga de borda está no caminho da requisição? | **Sim, síncrona.** `invalidaPorEvento` → `Invalidar` → `borda.Purga`: HTTP à API da Cloudflare, cliente com **timeout de 30 s**, lote de **100 URLs/chamada** | disco | `cmd/social/escrita.go:350-362`, `internal/socialpurga/invalidar.go:51,70`, `borda.go:24,66,82` |
| M6 | Concorrência do SQLite social | `journal_mode=wal`, `synchronous=2` (FULL), **`busy_timeout(5000)`** | disco (banco vivo) | `PRAGMA` em `?mode=ro`; `internal/socialdb/banco.go:160-163` |
| M7 | Vocabulário schema.org para alegação+evidência+veredito | **`ClaimReview` = 200**, `Claim` 200, `Comment` 200, `DiscussionForumPosting` 200, `Question` 200, `Answer` 200 | web/fonte oficial | `curl` em `https://schema.org/<tipo>` com UA do projeto (memória do repo: `LegalCase` deu 404 — por isso confirmei antes de nomear) |
| M8 | Existe registro de agente + credencial? | **Sim.** `EscopoRelatos = "relatos:escrever"` (único escopo), `CotaDiariaDeRegistro = 20`, rota `/agent/auth`, `/oauth/token`, `/oauth/jwks`, ledger `data/ops/oauth_clients.jsonl`, Ed25519 + JWKS | disco | `internal/oauthserver/oauthserver.go:46,157,176`; `internal/httpserver/oauth.go:34-40` |
| M9 | Existe precedente de escrita de agente com proveniência verificada? | **Sim.** `agentreports`: `CotaDiariaPorCliente = 50`, `CotaDiariaGlobal = 500`, campo **`trecho_confere_no_markdown`** (âncora literal contra o servido), allowlist `hostsOficiais = .gov.br .jus.br .leg.br .mp.br .def.br`, id determinístico | disco | `internal/agentreports/agentreports.go:79-80,109,170,294` |
| M10 | Quarentena e orçamento vivos (constantes que **não invento**) | `quarentena_conta_nova`: dias **7**, `posts_por_dia` **5**, `comentarios_por_dia` **20**, `posts_sobrevividos_para_sair` **3**, `link_externo_permitido` **false**, `mencoes_por_post` **2**. `orcamentos_diarios_por_conta`: posts **20**, comentários **100**. `indexacao.piso_de_corpo_em_caracteres` **1100** | disco | `content/social_policy.json` (`schema_version: social_policy_v1`, `vigente_desde: 2026-09-04`) |
| M11 | Precedente de alvo polimórfico já no banco | `reacoes(alvo_tipo, alvo_id)` com `CHECK (alvo_tipo IN ('duvida','resposta','post'))` + `idx_reacoes_alvo` | disco (banco vivo) | `.schema reacoes` |
| M12 | Falha do banco de contas no boot: laço ou degradação? | **Degrada.** `abreServicoDeConta` grava `servico.indisponivel` + `log.Printf` e retorna — **sem `log.Fatalf`**. Rede social continua no ar; só rotas de conta dão 503 | disco | `cmd/social/conta.go:144-176`, chamado em `superficie.go:437`; contrastar com `socialpolicy` (`log.Fatalf` + `Restart=always`) |
| M13 | Orçamento de bytes da página do tema (onde vive o comentário de autoridade) | **`TetoDeBytesDosComentarios = 30000`**, com corte por `ComentariosNaPagina()` no HTML e a gêmea lendo a lista **inteira** | disco | `internal/socialrender/telasdotema.go:262-292` |

**Não medido, nomeado:** o teto de **chamadas por hora** da API de purga da Cloudflare nesta
zona. O repositório documenta o teto de **100 URLs por chamada** (`borda.go:15-24`, citando
`developers.cloudflare.com/cache/how-to/purge-cache/#availability-and-limits`) e **não**
documenta teto por hora. É o primeiro número a medir (§6).

---

## 1. O MODELO DE DADO

### 1.1 O princípio: a alegação é um *span*, não uma cópia

Uma refutação que copiasse o texto refutado criaria uma segunda cópia que envelhece sozinha —
o defeito que este repositório já nomeou em `socialrender/exportacao.go:30-36` (1.756 bytes
servidos contra 1.230 montados para a mesma dúvida). Então a **alegação é um endereço**:
tipo de alvo, id do alvo e o trecho literal, conferido contra o corpo servido pela mesma
regra que `internal/agentreports` já aplica (`trecho_confere_no_markdown`,
`agentreports.go:109,306`) e que a extração do cérebro aplica em
`internal/cerebro/extracao.go:505` (126.601 de 126.601 itens ancorados).

### 1.2 Pacote novo: `internal/socialdebate`

Complemento de DDL **próprio**, versão **própria**, no mesmo arquivo de banco — o padrão que
`socialconteudo`, `socialautoridade`, `socialconexao`, `socialmail` e `verificacaooab` já
seguem, e pela razão que `socialautoridade/esquema.go:14-27` documenta: acrescentar tabela em
`socialdb.esquemaDoDominio` sem subir `socialdb.VersaoEsquema` é **no-op silencioso** contra
`var/social/social.db`, e subir aquela versão dispara a reconstrução dos doze passos sobre o
banco vivo.

```sql
-- (a) ALEGACOES — o endereço de uma afirmação dentro de um texto publicado.
CREATE TABLE IF NOT EXISTS alegacoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    alvo_tipo      TEXT    NOT NULL,
    alvo_id        INTEGER NOT NULL,
    trecho_citado  TEXT    NOT NULL,
    trecho_sha256  TEXT    NOT NULL,
    declarada_por  TEXT    NOT NULL,          -- conta_id (humana ou agente)
    criada_em      TEXT    NOT NULL,
    -- Vocabulário FECHADO, e a mesma forma de `reacoes` (precedente M11).
    -- 'refutacao' entra porque refutação de refutação é o contraditório, e sem
    -- ela o debate tem exatamente um turno.
    CHECK (alvo_tipo IN ('duvida','resposta','comentario_de_autoridade','refutacao','post')),
    CHECK (length(trim(trecho_citado)) > 0),
    CHECK (length(trecho_sha256) = 64),
    UNIQUE (alvo_tipo, alvo_id, trecho_sha256)
);
CREATE INDEX IF NOT EXISTS idx_alegacoes_alvo ON alegacoes(alvo_tipo, alvo_id, id);

-- (b) REFUTACOES — o elemento distintivo.
CREATE TABLE IF NOT EXISTS refutacoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    alegacao_id    INTEGER NOT NULL REFERENCES alegacoes(id) ON DELETE CASCADE,
    autor_conta_id TEXT    NOT NULL,
    veredito       TEXT    NOT NULL,
    tese           TEXT    NOT NULL,          -- o que o refutante afirma EM VEZ da alegação
    corpo          TEXT    NOT NULL,
    corpo_sha256   TEXT    NOT NULL,
    estado         TEXT    NOT NULL,
    criada_em      TEXT    NOT NULL,
    -- O VEREDITO É FECHADO, e é o análogo de `reviewRating` do ClaimReview (M7).
    -- Ele é o que separa "discordo" de "a norma foi revogada": as seis formas em
    -- que um jurista efetivamente contradiz outro, e nenhuma delas é uma nota.
    CHECK (veredito IN (
        'contradiz',                      -- afirma o oposto, com fundamento
        'distingue',                      -- o precedente não se aplica a este caso
        'confirma_parcialmente',          -- certo no núcleo, errado na extensão
        'superada_por_norma_posterior',   -- lex posterior
        'superada_por_precedente',        -- overruling / repetitivo novo
        'erro_de_citacao'                 -- o dispositivo citado não diz aquilo
    )),
    CHECK (estado IN ('publicada','em_moderacao','removida')),
    CHECK (length(trim(tese)) > 0),
    CHECK (length(trim(corpo)) > 0),
    CHECK (length(corpo_sha256) = 64),
    -- A cota que não precisa de tabela de orçamento — o MESMO padrão de
    -- comentarios_de_autoridade UNIQUE(perfil_id, tema_id)
    -- (socialautoridade/esquema.go:130): uma refutação por alegação por autor.
    -- Quem quiser dizer mais reescreve a própria.
    UNIQUE (alegacao_id, autor_conta_id)
);
CREATE INDEX IF NOT EXISTS idx_refutacoes_alegacao ON refutacoes(alegacao_id, estado, id);
CREATE INDEX IF NOT EXISTS idx_refutacoes_autor    ON refutacoes(autor_conta_id, id);

-- (c) FONTES_DA_REFUTACAO — a TERCEIRA instância do padrão de fonte normalizada
-- (fontes_da_resposta, fontes_do_comentario_de_autoridade), com os campos que as
-- duas primeiras NÃO têm e que o dossiê nomeou como lacuna ("falta medir o hash
-- da FONTE OFICIAL": a gêmea entrega URL e data em 40/40 e hash em 0/40).
CREATE TABLE IF NOT EXISTS fontes_da_refutacao (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    refutacao_id  INTEGER NOT NULL REFERENCES refutacoes(id) ON DELETE CASCADE,
    especie       TEXT    NOT NULL,
    nome          TEXT    NOT NULL,
    url           TEXT    NOT NULL,
    conferida_em  TEXT    NOT NULL,
    texto_sha256  TEXT,                  -- o sha do TEXTO OFICIAL conferido
    urn_lexml     TEXT,                  -- 98,9% dos itens do cérebro já têm URN
    numero_cnj    TEXT,                  -- processo público
    acordao_id    TEXT,                  -- id no espelho STJ (60.221 acórdãos)
    caminho_acervo TEXT,                 -- public_path de página nossa
    CHECK (especie IN ('dispositivo','sumula','acordao','tese_repetitivo','norma',
                       'processo','pagina_do_acervo')),
    CHECK (length(trim(nome)) > 0),
    CHECK (url LIKE 'https://%'),
    CHECK (texto_sha256 IS NULL OR length(texto_sha256) = 64)
);
CREATE INDEX IF NOT EXISTS idx_fontes_refutacao ON fontes_da_refutacao(refutacao_id);
CREATE INDEX IF NOT EXISTS idx_fontes_refutacao_urn ON fontes_da_refutacao(urn_lexml)
    WHERE urn_lexml IS NOT NULL;

-- (d) CASOS_EM_DISCUSSAO — o "caso real", e a trava é o CHECK.
--
-- ★ POR QUE NÃO HÁ conta_id AQUI, E POR QUE ISSO É A TRAVA
--
-- socialautoridade/esquema.go:39-51 recusa, por AUSÊNCIA de coluna, qualquer
-- vínculo entre texto de autoridade e o caso de alguém: LC 35/1979 (LOMAN)
-- art. 36, III veda ao magistrado opinar sobre processo pendente, e Lei 8.906/94
-- (EOAB) art. 28 torna a advocacia incompatível com a magistratura e o MP.
-- `TestEsquemaImpedePorAusencia` varre o banco VIVO atrás desses radicais.
-- Portanto: um caso em discussão é um ATO JUDICIAL PÚBLICO, nunca o caso de um
-- participante. Não há cliente, não há parte representada, não há encaminhamento.
CREATE TABLE IF NOT EXISTS casos_em_discussao (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cnj       TEXT    NOT NULL UNIQUE,
    tribunal         TEXT    NOT NULL,
    orgao_julgador   TEXT    NOT NULL DEFAULT '',
    classe           TEXT    NOT NULL DEFAULT '',
    assunto          TEXT    NOT NULL DEFAULT '',
    nivel_sigilo     INTEGER NOT NULL,
    -- `situacao` existe por causa da TRAVA 4: a vedação da LOMAN art. 36, III é
    -- sobre processo PENDENTE, e sem esta coluna a trava não tem o que ler.
    situacao         TEXT    NOT NULL,
    fonte_url        TEXT    NOT NULL,
    coletado_em      TEXT    NOT NULL,
    CHECK (situacao IN ('pendente','julgado','transitado')),
    -- ESTE CHECK É A MUDANÇA DE CATEGORIA. Hoje a recusa por sigilo é um `if` em
    -- cmd/social/processotela.go (CPC art. 189, `nivelSigilo > 0`). Um `if` vale
    -- para o caminho que o chama; um CHECK vale para o arquivo. Processo em
    -- segredo de justiça não PODE fisicamente entrar nesta tabela — nem por
    -- handler apressado, nem por carga de dado, nem por script de correção.
    CHECK (nivel_sigilo = 0),
    CHECK (length(trim(numero_cnj)) > 0),
    CHECK (fonte_url LIKE 'https://%')
);

-- (e) VINCULOS_DO_CASO — o caso ↔ a discussão, e o caso ↔ o acervo.
CREATE TABLE IF NOT EXISTS vinculos_do_caso (
    caso_id    INTEGER NOT NULL REFERENCES casos_em_discussao(id) ON DELETE CASCADE,
    alvo_tipo  TEXT    NOT NULL,
    alvo_id    INTEGER NOT NULL,
    criado_em  TEXT    NOT NULL,
    PRIMARY KEY (caso_id, alvo_tipo, alvo_id),
    CHECK (alvo_tipo IN ('duvida','refutacao','post','tema'))
);
```

### 1.3 As travas que são TRIGGER, e por que cada uma

O padrão é o de `socialautoridade/esquema.go:153-215`: a regra que a plataforma **afirma em
público** mora no banco, não num `if`.

```sql
-- TRAVA 1: o trecho da alegação é IMUTÁVEL. Sem ela, um UPDATE trocaria o texto
-- que a refutação contesta, e uma refutação publicada passaria a contestar outra
-- coisa. É o mesmo raciocínio de comentarios_de_autoridade_ancora_e_imutavel.
CREATE TRIGGER IF NOT EXISTS alegacoes_trecho_e_imutavel
BEFORE UPDATE ON alegacoes
WHEN new.trecho_citado <> old.trecho_citado OR new.alvo_tipo <> old.alvo_tipo
  OR new.alvo_id <> old.alvo_id
BEGIN
    SELECT RAISE(ABORT, 'o alvo e o trecho de uma alegacao sao imutaveis: trocalos faria a refutacao publicada contestar texto que ninguem escreveu');
END;

-- TRAVA 2: refutação publicada EXIGE ao menos uma fonte. É a diferença entre
-- refutação e discordância, e é a inversão do prêmio à vagueza que a medição
-- desta sessão pegou (a peça APROVADA foi a que trocou "REsp 1.794.991" por
-- "a jurisprudencia relevante diferencia").
--
-- ★ SÃO DOIS TRIGGERS, E O DO INSERT NÃO É REDUNDANTE
--
-- `fontes_da_refutacao REFERENCES refutacoes(id)` significa que a fonte NÃO PODE
-- existir antes da linha. Logo a escrita é necessariamente em dois passos:
--   1. INSERT em refutacoes com estado='em_moderacao'
--   2. INSERT das fontes
--   3. UPDATE para estado='publicada'  <- é aqui que a TRAVA 2a confere
-- Um trigger só de UPDATE deixa aberto o INSERT que já nasce 'publicada' — e
-- então a linha nunca passa pela conferência. É EXATAMENTE o furo que
-- `duvidas_banda_exige_verificado_insert` (socialconteudo/esquema.go:109-115)
-- existe para fechar, com a mesma forma: o INSERT com o estado final já posto é
-- recusado INCONDICIONALMENTE, porque aquele estado é conquistado por transição,
-- nunca declarado na origem.
CREATE TRIGGER IF NOT EXISTS refutacoes_publicada_exige_fonte_update
BEFORE UPDATE OF estado ON refutacoes
WHEN new.estado = 'publicada'
BEGIN
    SELECT RAISE(ABORT, 'refutacao sem fonte oficial normalizada nao se publica: alegacao contestada sem evidencia e discordancia, e discordancia nao e refutacao')
    WHERE NOT EXISTS (SELECT 1 FROM fontes_da_refutacao f WHERE f.refutacao_id = new.id);
END;

CREATE TRIGGER IF NOT EXISTS refutacoes_publicada_exige_fonte_insert
BEFORE INSERT ON refutacoes
WHEN new.estado = 'publicada'
BEGIN
    SELECT RAISE(ABORT, 'refutacao nao nasce publicada: a fonte referencia a propria linha e so pode ser gravada depois dela, entao publicar e uma TRANSICAO conferida, nunca um estado declarado no INSERT')
    WHERE 1 = 1;
END;

-- TRAVA 3: o autor de uma refutação NUNCA é o autor da alegação contestada —
-- auto-refutação é erratum, e erratum se faz reescrevendo o próprio texto.
--
-- ★ ENUMERA OS CINCO VALORES DO CHECK, E NÃO TRÊS
--
-- Guarda pela metade é guarda que responde ao grep e não cobre o par que
-- importa. `alvo_tipo` admite cinco valores e os cinco têm autor: `duvidas`,
-- `respostas`, `comentarios_de_autoridade`, `refutacoes` e `posts_blog` todos
-- carregam `autor_conta_id`. O teste de mutação ITERA o vocabulário do CHECK —
-- valor novo sem ramo aqui reprova, em vez de passar em silêncio.
CREATE TRIGGER IF NOT EXISTS refutacoes_nao_refuta_o_proprio_texto
BEFORE INSERT ON refutacoes
BEGIN
    SELECT RAISE(ABORT, 'nao se refuta o proprio texto: corrigir o que se escreveu e reescrever, e a rede registra a reescrita, nao um debate consigo mesmo')
    WHERE EXISTS (
        SELECT 1 FROM alegacoes a
        WHERE a.id = new.alegacao_id AND (
            (a.alvo_tipo = 'resposta'   AND EXISTS (SELECT 1 FROM respostas  r WHERE r.id = a.alvo_id AND r.autor_conta_id = new.autor_conta_id)) OR
            (a.alvo_tipo = 'duvida'     AND EXISTS (SELECT 1 FROM duvidas    d WHERE d.id = a.alvo_id AND d.autor_conta_id = new.autor_conta_id)) OR
            (a.alvo_tipo = 'refutacao'  AND EXISTS (SELECT 1 FROM refutacoes x WHERE x.id = a.alvo_id AND x.autor_conta_id = new.autor_conta_id)) OR
            (a.alvo_tipo = 'post'       AND EXISTS (SELECT 1 FROM posts_blog p WHERE p.id = a.alvo_id AND p.autor_conta_id = new.autor_conta_id)) OR
            (a.alvo_tipo = 'comentario_de_autoridade'
                                        AND EXISTS (SELECT 1 FROM comentarios_de_autoridade c WHERE c.id = a.alvo_id AND c.autor_conta_id = new.autor_conta_id))
        )
    );
END;

-- TRAVA 4: magistrado e membro do MP não refutam sobre PROCESSO PENDENTE.
--
-- LC 35/1979 (LOMAN), art. 36, III veda ao magistrado manifestar opinião sobre
-- processo PENDENTE de julgamento, e RESSALVA no mesmo inciso a crítica em obra
-- técnica ou no magistério. A ressalva é o que autoriza o jurista a participar
-- desta rede; o "pendente" é o que a trava tem de enxergar. Sem a coluna
-- `situacao` e sem este trigger, a plataforma construiria o caminho da infração
-- funcional — o mesmo raciocínio das TRAVAS 2 e 3 de socialautoridade.
CREATE TRIGGER IF NOT EXISTS refutacoes_jurista_nao_opina_sobre_pendente
BEFORE INSERT ON refutacoes
BEGIN
    SELECT RAISE(ABORT, 'magistratura e ministerio publico nao se manifestam sobre processo pendente de julgamento: LC 35/1979 (LOMAN) art. 36, III, cuja ressalva alcanca a critica tecnica, nao o caso em curso')
    WHERE EXISTS (
        SELECT 1
          FROM perfis p
          JOIN perfis_jurista j ON j.perfil_id = p.id
          JOIN alegacoes  a ON a.id = new.alegacao_id
          JOIN vinculos_do_caso v ON v.alvo_tipo = a.alvo_tipo AND v.alvo_id = a.alvo_id
          JOIN casos_em_discussao c ON c.id = v.caso_id
         WHERE p.conta_id = new.autor_conta_id
           AND j.funcao IN ('magistratura', 'ministerio_publico')
           AND c.situacao = 'pendente'
    );
END;
```

### 1.4 A trava que é a AUSÊNCIA de um caminho

**Uma refutação nunca é uma linha em `respostas`.** Medi o motivo: o trigger
`duvidas_banda_exige_verificado_update` (`socialconteudo/esquema.go:96-107`) tira a dúvida da
banda `aguardando` quando existe `respostas` publicada de perfil com `perfis_advogado` — e
**só conta `respostas`**. Se a refutação fosse uma resposta, um agente refutando promoveria a
dúvida a "respondida por advogado com inscrição verificada": afirmação falsa sobre habilitação
profissional exposta ao público. Tabela própria fecha esse caminho por construção, e a trava
é o trigger existente, não um `if` novo.

### 1.5 O vínculo com o acervo: só por identificador externo estável

`internal/socialisolation` reprova `cmd/social` importar o roteador do acervo. Então o
vínculo é **por identificador**, nunca por FK entre arquivos:

| Objeto do acervo | Chave usada | Onde já existe |
|---|---|---|
| dispositivo legal | **URN LexML** | `content/legal_cocitation_index.jsonl` (1.059 URNs), extrações do cérebro (98,9% com URN) |
| súmula / tese | URN / `stj/tema/N` | painel de precedente, `cmd/social/antes.go` |
| acórdão | `acordao_id` do espelho | `data/corpus/jurisprudencia/stj-espelhos/` (60.221) |
| processo | número CNJ | `cmd/social/processotela.go` (DataJud ao vivo) |
| página nossa | `public_path` | `published_manifest.jsonl` (11.106) |
| identidade externa | **QID Wikidata** | `data/corpus/wikidata/lexml_qids.jsonl` (38.018 QIDs, 93,0% dos dispositivos do grafo) — hoje em superfície nenhuma |

As arestas `supera` / `altera` / `impactada_por` do grafo (`data/ai/grafo.sqlite`) valem **0 de
393.081** hoje. Elas **não** se escrevem daqui: o cérebro as **deriva** das refutações, a
jusante, com `veredito IN ('superada_por_norma_posterior','superada_por_precedente')` como
fonte. A refutação passa a ser o produtor do sinal de divergência que o grafo declara no
schema e nunca teve.

---

## 2. A IDENTIDADE DO AGENTE

### 2.1 A decisão de fundo, e a medição que a forçou

Medi (M3): `contas` exige `email_indice`, `email_cifrado` e `senha_phc` NOT NULL, e o `papel`
tem `CHECK IN ('leigo','advogado','jurista')`. Um agente não tem e-mail nem senha. Duas rotas:

- **Autor polimórfico** (agente num namespace próprio): recusada. Toda coluna de autor da rede
  é `autor_conta_id TEXT` — `duvidas`, `respostas`, `comentarios_de_autoridade`, `notificacoes`,
  `reacoes`, `quarentena`, `orcamento_diario`, `fila_moderacao`. Polimorfismo tocaria todas e
  quebraria todo trigger existente.
- **Agente É uma conta, com discriminador honesto**: escolhida. Quarentena, orçamento diário,
  reputação, moderação e notificações passam a valer para agentes **de graça, no primeiro dia**.

### 2.2 `contas` SchemaVersion 1 → 2

`internal/contas/contas.go:83` (`SchemaVersion = 1`) e `esquema.go:46-51` (recusa abrir se a
versão divergir). A migração:

```sql
ALTER TABLE contas ADD COLUMN especie TEXT NOT NULL DEFAULT 'humana';
ALTER TABLE contas ADD COLUMN cliente_oauth_id TEXT;   -- UNIQUE por índice parcial
-- e a reconstrução de tabela (SQLite não altera CHECK) que:
--   papel      CHECK (papel IN ('leigo','advogado','jurista','agente'))
--   especie    CHECK (especie IN ('humana','agente'))
--   email_indice / email_cifrado / senha_phc  passam a NULLABLE
-- COM O INVARIANTE HUMANO NA MESMA FORÇA DE HOJE:
--   CHECK (especie <> 'humana' OR (email_indice IS NOT NULL
--                              AND email_cifrado IS NOT NULL
--                              AND senha_phc    IS NOT NULL))
-- E COM O CAMINHO DE SENHA FECHADO PARA AGENTE, POR CONSTRUÇÃO:
--   CHECK (especie <> 'agente' OR (senha_phc IS NULL
--                              AND email_indice IS NULL
--                              AND cliente_oauth_id IS NOT NULL))
--   CHECK (especie <> 'agente' OR papel = 'agente')
CREATE UNIQUE INDEX idx_contas_cliente_oauth ON contas(cliente_oauth_id)
    WHERE cliente_oauth_id IS NOT NULL;
```

**M12 — MEDI o modo de falha, e ele NÃO é laço de boot.** `esquema.go:46-51` recusa nas duas
direções (`ErrVersaoAdiante` para binário velho/banco novo, `ErrEsquemaDesatualizado` para
binário novo/banco velho). A pergunta que importa é o que o `cmd/social` faz com essa recusa:
`superficie.go:437` chama `abreServicoDeConta`, e `cmd/social/conta.go:167-175` trata a falha de
`contas.AbrirNaConexao` gravando `servico.indisponivel` e **logando** — `return servico`, sem
`log.Fatalf`. **A superfície pública continua no ar; só as rotas de conta respondem 503.**

Isso é materialmente diferente do `social_policy.json` (§5.2), que **é** `log.Fatalf` com
`Restart=always`. A ordem de implantação do passo 5, mesmo assim, é numerada — porque a
direção `ErrVersaoAdiante` (migrar o banco antes de trocar o binário) degradaria as contas dos
humanos até o swap:

```
1. ensaio da migração sobre cópia VACUUM INTO do banco vivo   (nunca sobre o vivo)
2. binário com SchemaVersion = 2 e com a função que SABE MIGRAR, no disco
3. swap do binário         (./tools/deploy-binario-go)
4. a migração roda no boot do binário novo, sobre o banco na v1
5. conferir: `select versao from esquema_contas` = 2, e as rotas de conta
   fora de `indisponivel` (o log do processo diz qual dos dois)
```

Migrar o banco no passo 1 e trocar o binário depois inverte isso e produz `ErrVersaoAdiante`
na janela entre os dois — contas indisponíveis por minutos, sem queda da rede.

**Por que não um e-mail sintético.** Um endereço em `.invalid` (RFC 6761) faria a coluna
"e-mail da pessoa" carregar um valor que não é o e-mail de ninguém — string fake numa coluna
de dado real, proibida pelo contrato. Um CHECK amarrado ao discriminador é a forma honesta, e
o **controle positivo** prova que não afrouxou nada: linha `especie='humana'` sem e-mail
continua sendo recusada pelo banco.

**Ganho de segurança, não perda:** um agente **não tem hash de senha**. Não há caminho de
`/api/v1/redesocial/conta/entrar`, de recuperação nem de OTP que alcance uma conta de agente —
o `CHECK (senha_phc IS NULL)` fecha isso no arquivo. A credencial é o cliente OAuth.

### 2.3 O quinto papel, linha por linha

`internal/socialpapeis/papeis.go` — os quatro papéis são fechados e cobrados por teste de
mutação. `PapelAgente Papel = "agente"` exige, **nominalmente**:

| Linha | Mudança | Valor e por quê |
|---|---|---|
| `papeis.go:67` `papeisConhecidos` | acrescenta `PapelAgente` | ordem crescente de alcance: depois de `PapelVisitante`, antes de `PapelLeigo` — agente escreve, mas nunca recebe caso nem assina autoridade |
| `papeis.go:92` `Rotulo()` | `"agente participante"` | o que o visitante lê; vocabulário visível ao público, com acento |
| `papeis.go:113` `recebemCaso` | `PapelAgente: false` | **a trava**. Agente não é destinatário de caso |
| `papeis.go:164` `Deriva` switch | `case contas.PapelAgente` | devolve `PapelAgente` quando `ContaAtiva`; **e recusa** `SeloDeOABVigente` sobre conta de agente com `ErrIdentidadeIncompativel` — a inscrição na OAB é de pessoa natural bacharel (Lei 8.906/94, art. 8º), então selo vigente sobre conta de agente é dado corrompido, não estado possível |
| `papeis.go:226` `ImpedimentoDe` | fundamento nomeado | `"Lei 8.906/94 (EOAB), art. 1º e art. 8º, I e II"` — postular e consultar é privativo de advogado inscrito, e a inscrição exige pessoa natural com capacidade civil e diploma; um agente não pode ter inscrição, então não pode receber caso |
| `papeis.go:260` `PodeAssinarConteudoDeAutoridade` | `false` para agente | **inegociável**. O selo de autoridade é afirmação da plataforma sobre função pública ou inscrição conferida; agente não tem nenhuma das duas. O texto do cérebro que sai sob a assinatura do advogado continua entrando por `cmd/social/interno.go` (DEC-059) — esse caminho não muda |
| `papeis_test.go` | caso de mutação novo | copiar `recebemCaso`, pôr `PapelAgente: true`, provar que o caso passaria a ser encaminhado; controle positivo sobre a tabela real |

E `internal/socialautoridade/esquema.go`: as TRAVAS 2 e 3 (incompatibilidade jurista ↔
advogado) ganham a terceira aresta — **conta de agente não recebe `perfis_advogado` nem
`perfis_jurista`**, por trigger, pela mesma razão pela qual as outras duas existem.

### 2.4 Os três tiers de verificação, cada um com a medição que o sustenta

| Tier | Como se identifica | O que pode | Constante, e de onde vem |
|---|---|---|---|
| **T0 — não identificado** | nada | **Lê tudo o que é público. Escreve nada.** | É o estado atual de **144.524 requisições de IA em 8 dias (45,1% do externo)**. Quebrar a leitura anônima destruiria a única demanda medida que o projeto tem |
| **T1 — registrado** | cliente OAuth de `/agent/auth` (`oauth.go:38`) + token com o escopo novo | Escreve **em quarentena** | `quarentena_conta_nova` viva: **7 dias, 5 publicações/dia, 20 comentários/dia, sai com 3 publicações sobrevividas, sem link externo** (M10). Zero número inventado |
| **T2 — verificado** | (a) assinatura HTTP RFC 9421 cuja chave resolve no diretório do próprio agente (Web Bot Auth, `draft-ietf-webbotauth-httpsig-protocol-00`, documento de WG desde 2026-09-01) **ou** (b) IP em faixa oficial publicada (`data/ops/bot_ip_ranges/*.json`) | Sai da quarentena no limiar medido; orçamento diário pleno | `orcamentos_diarios_por_conta`: **20 publicações, 100 comentários** (M10) |

**Quarentena não é castigo, é o desenho existente.** `socialantiabuso` e a tabela `quarentena`
(`conta_id`, `inicio_em`, `publicacoes_sobreviventes`) já implementam isso para humanos novos.
Agente entra pela mesma porta. É a lição que a Moltbook pagou e publicou: 2.895.874 agentes
registrados contra 206.839 verificados (92,9% sem verificação), 1,5 M de tokens vazados,
injeção de prompt em 2,6% dos posts. **Identidade criptográfica antes do primeiro post.**

### 2.5 Os dois lados do Web Bot Auth

- **Como verificador (entrada):** conferir `Signature`, `Signature-Input` e `Signature-Agent`
  sobre a base de assinatura mínima da RFC 9421 (`@method @authority @path content-digest
  signature-agent`). `Content-Digest` é RFC **9530** — a **mesma família** do `Repr-Digest` que
  `/api/v1/citar` já emite (`internal/httpserver/api_citar.go`), então não é vocabulário novo
  no projeto, é reuso. Subconjunto pequeno: implementar à mão, ou ADR com licença e versão
  fixada se for biblioteca — dependência nova de runtime exige ADR pelo contrato.
- **Como cliente (saída):** publicar nosso `/.well-known/http-message-signatures-directory`
  (**medido 404 hoje**) e assinar a saída do `WikijuridicaBot`. Isso dá identidade verificável
  contra WAF — exatamente o caso do F5 BIG-IP do Planalto que já nos recusou.

**A armadilha que eu mesmo criaria, e o conserto.** Verificar T2 exige buscar o diretório de
chaves em `https://<Signature-Agent>/.well-known/http-message-signatures-directory` — ou seja,
**uma requisição HTTP de saída dentro do caminho de escrita**, que é exatamente a classe de
defeito que §6.2 nomeia como o primeiro penhasco deste sistema. Então: **cache por `kid` com
TTL**, populado fora do caminho da requisição; chave desconhecida rebaixa para **T1** (escreve
em quarentena) em vez de bloquear ou de esperar a rede. E a saída vai por
`wikijuridicabot.Aplica(req, proposito)` — nunca um User-Agent escrito à mão, que é cobrado por
`TestNenhumPontoDeSaidaSaiDisfarcado`.

### 2.6 O rate limit que NÃO pode herdar o bypass

Medido em `internal/socialborda/rate.go:14-18`: `$wj_generic_key` e `$wj_bot_allow` ficam
**vazias** para bot allowlistado, e **requisição com chave vazia não é contada por zona
nenhuma**. Ou seja: se a rota de escrita de agente herdar as zonas derivadas de User-Agent,
todo agente valioso escreve **sem limite**.

A rota de escrita **chaveia pelo `client_id` do token**, nunca pelo UA. O precedente já está
no disco: `agentreports.CotaDiariaPorCliente = 50` + `CotaDiariaGlobal = 500` (M9) — cota
por cliente **e** global, porque cota só por cliente é contornável registrando vinte clientes
(e `CotaDiariaDeRegistro = 20` é o teto que fecha esse loop).

**E 429 é obrigatório.** `socialborda/rate.go:116-120` já reprova `limit_req_status` diferente
de 429: "o cliente limitado precisa receber 429 para saber que deve voltar depois". Medição da
sessão: **429 = ZERO em 8 dias** em todo agente. Não há perda a recuperar hoje; quando a
escrita existir, 429 é o sinal honesto.

---

## 3. AS ROTAS, NAS DUAS SERIALIZAÇÕES

### 3.1 São DOIS documentos, não um — e o principal é o do tema

A refutação não entra como rota: entra como **campo novo de um documento existente**. Mas
`alvo_tipo` tem cinco valores e eles **não caem todos no mesmo documento**. Medi onde cada
alvo é renderizado:

**(A) Alvos da thread** — `duvida`, `resposta`, `refutacao`. Campo novo em
`socialrender.DocumentoDaDuvida` (`duvida.go:134-143`), e daí cinco canais por construção:

| Canal | Onde | O que renderiza |
|---|---|---|
| HTML da thread | `cmd/social/thread.go:84` | `socialrender/duvida.go` |
| Gêmea Markdown | `thread.go:104` | `MarkdownDaDuvida` |
| Exportação (anexo) | `thread.go:140` | **byte a byte a gêmea**, por desenho (`exportacao.go:66-80`) |
| Atom da thread | `thread.go:175` | `socialconteudo.Atom` |
| MCP `ler_duvida` | `mcp_social.go:846` `markdownDaDuvida` | o mesmo documento |

**(B) Alvo do tema** — `comentario_de_autoridade`, e **este é o caso principal**, não o
acessório: o comentário de autoridade vive na página do TEMA
(`socialrender/telasdotema.go:274,322`, seção `#comentarios-de-autoridade`), que é a superfície
com **11.299 req/dia na borda (12,8% da zona)** e é **onde o cérebro publica** pelo DEC-059.
Refutar o que a autoridade afirmou é o evento central desta rede. Canais próprios:

| Canal | Onde |
|---|---|
| HTML do tema | `cmd/social/tema.go:86` |
| Gêmea Markdown do tema | `tema.go:99` (`sufixoDaGemeaDoIndice`) |
| Atom do tema | `cmd/social/atom.go:112` — **12.180 req/dia medidas** |
| MCP `duvidas_do_tema` | `mcp_social.go:1044` |

**E o tema tem orçamento de bytes, medido:** `socialrender.TetoDeBytesDosComentarios = 30000`
(`telasdotema.go:262`), com `ComentariosNaPagina()` cortando o que não cabe no HTML e a gêmea
lendo a lista **inteira** — divergência deliberada, porque a gêmea não paga o teto de 50 KB.
**A refutação entra no mesmo orçamento e pela mesma regra**, com a mesma consequência:
refutação que não cabe no HTML continua alcançável por máquina no mesmo instante. Isso reusa
`ComentariosOmitidos()` (`:292`) em vez de inventar uma segunda política de corte.

**(C) `post`** — `posts_blog`, canais em `cmd/social/posts.go:98-116`.

**Testes de paridade a estender no MESMO commit, dos dois lados:**
`internal/socialmarkdown/paridade_test.go`, `internal/httpserver/mcp_paridade_tres_vias_test.go`,
`cmd/social/thread_jsonld_test.go`, `internal/socialrender/gemea_test.go`,
`internal/socialrender/orcamento_dos_comentarios_test.go` (o teto de 30 KB) e
`cmd/social/tema_test.go`. Sem isso, o campo novo aparece em três canais e falta em dois — o
defeito que a §7 do contrato nomeia e que nenhum teste enxerga quando não há com o que comparar.

### 3.2 Rotas de escrita (novas, mínimas)

```
POST /api/v1/redesocial/agente/alegacao     -> 201 {alegacao_id, trecho_sha256, urn}
POST /api/v1/redesocial/agente/refutacao    -> 201 {refutacao_id, url, urn, corpo_sha256}
POST /api/v1/redesocial/agente/duvida       -> 201 (agente pergunta; mesma régua do leigo)
```

**Por que `/api/v1/redesocial/` e não `/redesocial/`:** `socialrender/exportacao.go:57-63`
documenta que a regra de Dynamic Redirect da Cloudflare **acrescenta barra final** a todo
caminho sob `/redesocial/` que não a tenha e não termine em extensão isenta. **Um POST que leva
301 é um POST morto.** E aquele prefixo já tem `limit_req zone=wj_social_escrita`
(`ops/nginx/social-headers-publico.conf:43`) e já aterra no processo social na 8091 — é onde
`/api/v1/redesocial/csp-report` vive hoje (`cmd/social/cspreport.go:549`), enquanto
`/api/v1/redesocial/lote` é servido pelo `cmd/server` na 8089 em `?mode=ro`
(`mcp_social.go:191`). A escrita **tem** de aterrar na 8091.

Autorização: **não** `sv.conta.escrita(...)` (cookie `wjsession` + `X-WJ-CSRF`, que um agente
não tem por construção — o próprio `interno.go:13-22` documenta isso). É `Bearer` do
`oauthserver`, com o escopo novo, mais a assinatura RFC 9421 para T2.

### 3.3 Rotas de leitura (estender, não criar)

| Rota | Estado medido | O que muda |
|---|---|---|
| `/api/v1/redesocial/lote` | armada desde 2026-09-09 (`agentsurface.go:160-166`); **17 chamadas externas em 8 dias** | ganha `tipo: "refutacao"` no NDJSON. Contrato de forma preservado: NDJSON, linha final `{"tipo":"fim"}`, tetos 50/200, `lastmod` crescente, cursor resolvido a cada chamada |
| `/api/v1/citar/redesocial/duvida/{slug}/` | **404 medido (M1)** | passa a 200 com o mesmo schema de 15 campos do acervo. **Extensão, não endpoint novo** |
| `/redesocial/tema/{area}/{slug}/feed.xml` | **12.180 req/dia**, 95,4% GPTBot+Amazonbot | corpo completo da refutação, URN LexML, link para a gêmea. É o canal que a IA **já escolheu**, com custo zero de descoberta |
| MCP `ler_duvida` / `duvidas_do_tema` | vivas (`mcp_social.go:1001,1044`) | passam a trazer as refutações no mesmo Markdown |
| `/redesocial/llms.txt` | vivo (`cmd/social/agentes.go:79`) | a lista é **derivada das constantes**, então rota nova entra sozinha — e `agentes_test.go` pede cada link ao mux real e reprova 404/405 |

### 3.4 MCP: duas ferramentas novas e a capability que falta

```
refutar(alvo, trecho_citado, veredito, tese, corpo, fontes[])   -> escrita, exige escopo
ler_refutacoes(caminho | slug, limite)                          -> leitura, anônima
```

Hoje o servidor anuncia **15 ferramentas** e `capabilities` = **2 (`logging`, `tools`)**, com
**zero `resources`** sobre 11.106 páginas. Uma refutação é um `resource` natural (URI estável,
`mimeType: text/markdown`, assinável por `resources/subscribe`). O gate que falta e que o
dossiê nomeou: **igualdade entre os três inventários de capacidade** — `tools/list` (15),
`/.well-known/agent-skills/index.json` (14) e o agent-card A2A (4 skills). `agentsurface` é
fonte única das **rotas** e nada cobra as **capacidades**, que é exatamente o defeito que o
pacote existe para prevenir (`agentsurface.go:14-21`).

### 3.5 O que entra em `internal/agentsurface`

`ServicosDaRedeSocial` (`agentsurface.go:174`) é a **fonte única** e ganha as rotas de leitura
novas. As de **escrita ficam fora**, pela razão que o próprio arquivo documenta em
`agentes.go:32-33`: um índice de leitura que anunciasse superfície de POST convidaria o agente
a um 405. Elas entram no **OpenAPI** e no **agent-card**, que são os documentos de capacidade.

**Cuidado medido:** `TestSuperficieDeAgenteSoAnunciaRotaViva` pede **cada** entrada de
`Servicos` ao roteador real. Rota anunciada antes de existir reprova — e `ServicosDaRedeSocial`
é separada justamente porque a capacidade é **condicional** (sem o banco social, a rota não
nasce).

---

## 4. CITABILIDADE

### 4.1 O identificador estável inclui a VERSÃO do texto

```
urn:wj:redesocial:refutacao:{id}:{corpo_sha256[0:16]}
urn:wj:redesocial:alegacao:{alvo_tipo}:{alvo_id}:{trecho_sha256[0:16]}
```

O hash **dentro** do identificador é a decisão de desenho: um LLM que cita
`urn:wj:redesocial:refutacao:4182:9f3c1ab0e7d25648` cita **aquele texto**, não "a refutação
4182, o que ela for hoje". Refutação editada muda de URN — a citação nunca aponta em silêncio
para texto trocado. É a mesma garantia que `html_sha256`/`markdown_sha256` já dão à página
(medido em M1: os dois batem com os bytes servidos nas duas pontas).

### 4.2 O bloco "Como citar", e a alavanca que ele corrige

Medição do dossiê: o aparato de citação (ABNT + sha256 + CSL-JSON + licença) está em **40 de
40 gêmeas e 0 de 40 HTMLs**, enquanto **3.352 requisições/24 h** de quem produz resposta ao
vivo chegam ao HTML e só **26 (0,8%)** passam pela gêmea. Então a refutação nasce com o bloco
de citação nos **dois** canais — não repetindo o erro de origem.

Campos, todos derivados de coisa que já existe:

| Campo | Fonte no repo |
|---|---|
`referencia_abnt` | `api_citar.go` (formato já emitido para o acervo)
`cite_as` (CSL-JSON) | `mcp_contexto.go` (já emite `cite_as`)
`corpo_sha256`, `Repr-Digest` | RFC 9530, já em `api_citar.go`
`licenca` | CC-BY-4.0, já declarada em `contexto_juridico`
`autor` | `perfis` + `verificacaooab.Selo` (nunca coluna booleana)
`fontes[].texto_sha256` | **novo**, e fecha a lacuna nomeada: a gêmea entrega URL e data em 40/40 e hash em **0/40**

### 4.3 JSON-LD: `ClaimReview` (verificado 200 hoje — M7)

```jsonc
{
  "@context": "https://schema.org",
  "@type": "ClaimReview",
  "url": "https://wikijuridica.com.br/redesocial/duvida/{slug}/#refutacao-{id}",
  "identifier": "urn:wj:redesocial:refutacao:{id}:{sha16}",
  "datePublished": "{criada_em}",
  "claimReviewed": "{trecho_citado}",
  "itemReviewed": {
    "@type": "Claim",
    "appearance": { "@type": "CreativeWork", "url": "{url do alvo}#{ancora}" }
  },
  "reviewRating": {
    "@type": "Rating",
    "alternateName": "{veredito}",      // vocabulário FECHADO da §1.2
    "ratingExplanation": "{tese}"
  },
  "author": { /* ver o cuidado 3, abaixo — NÃO é sempre o advogado */ },
  "citation": [ { "@type": "Legislation", "url": "...", "legislationIdentifier": "{urn_lexml}" } ]
}
```

Três cuidados **medidos** neste repositório:
1. **`reviewRating` NÃO é nota de mérito de ninguém.** `Provimento CFOAB 205/2021, art. 5º`
   veda ranking e nota, e `internal/socialautoridade` recusou coluna de nota por ausência. O
   `alternateName` carrega o **veredito jurídico sobre a alegação** (`contradiz`, `distingue`…),
   nunca uma pontuação de participante. O `ratingValue` numérico **fica de fora**.
2. **JSON-LD novo no HTML ⇒ `--ressemear`** (matriz da §6 do contrato: mudança de markup
   servido). Na gêmea, não.
3. **`author` é quem de fato assina, e a inscrição não se repete.** Refutação de agente assina
   como **o agente** (`PapelAgente`, §2.3) — jamais como o advogado; só o texto do cérebro que
   sai por `interno.go` leva a assinatura do titular (DEC-059). E há um teto medido:
   `internal/render/author_credential_test.go` exige **exatamente duas** ocorrências visíveis de
   `OAB/<seccional> <número>` por página, pela sobriedade do Provimento 205/2021 — **uma
   terceira reprova**. Com N refutações numa página de tema, N blocos de JSON-LD com o
   `identifier` da OAB estourariam isso na hora. **Verificação obrigatória antes do passo 15:**
   ler se aquele teste conta JSON-LD ou só texto visível, e se existe equivalente do lado
   social. Se contar, o `identifier` da OAB sai do JSON-LD por refutação e fica **uma vez só**,
   no `author` do documento.

### 4.4 A lacuna que isto fecha: âncora por bloco

`internal/pagemarkdown/fidelidade_test.go:70-90` já cobra H2↔seções e H3↔FAQ **sobre o acervo
real** — os blocos são estáveis por contrato, não por acaso. Então `#{ancora}` + hash por bloco
é barato e entrega `/api/v1/trecho/{path}#{ancora}`: hoje há sha256 da **página inteira** e
nenhuma âncora estável por seção, e um agente que cita um parágrafo não pode apontar para ele
nem provar que não mudou. **É o único ponto em que o LexML bate este acervo** — ele resolve por
URN até o dispositivo; aqui, até a página.

---

## 5. O VÍNCULO COM O QUE JÁ EXISTE

### 5.1 O cérebro como moderador: estender `interno.go`, nunca um segundo canal

`cmd/social/interno.go:399-406` despacha por `pedido.Tipo`, hoje dois valores. Ganha:

```go
tipoRefutacao          = "refutacao"
tipoDecisaoDeModeracao = "decisao_de_moderacao"
```

**Por que no mesmo socket.** O cabeçalho de `interno.go:24-33` já escreveu a lição: *"Um
segundo gate aqui seria uma segunda verdade sobre o mesmo texto, e a lição já paga deste
repositório é que a verdade duplicada diverge no primeiro ajuste que só um dos dois lados
recebe."* O socket já traz, de graça: HMAC-SHA256 sobre o **corpo exato** conferido **antes do
parse** (`interno.go:360-367`), ledger idempotente por sha256 (`chaveIdempotenteValida`,
`:429`), serialização por `publicarMu` (`:237-243`), e o gate rodando **dentro da transação**.

`rotaDaDecisaoDeModeracao` (`cmd/social/moderacao.go:200`) está hoje atrás de
`sv.conta.leitura/escrita` — sessão humana. Com `decisao_de_moderacao` no socket, o cérebro
decide pela fila **sem** que "revisão humana como etapa de esteira" exista, que é a ordem em
vigor. A trilha permanece: `trilha_moderacao` + `var/social/cerebro_ledger.jsonl`.

### 5.2 `content/social_policy.json`: a ORDEM É LEI

Medido: `internal/socialpolicy/policy.go` faz `decoder.DisallowUnknownFields()` no `Load`,
`cmd/social` faz `log.Fatalf` se a política reprova, e a unit tem `Restart=always`. **JSON
antes do binário = laço de boot da rede social inteira** (foi o que aconteceu em 2026-09-09 com
`habitualidade_modo` e `destrava_abrir_thread: 0`).

Seção nova `refutacao`, e a ordem obrigatória, como **passo de implementação numerado**, não
como nota de pé:

```
1. binário novo NO DISCO (com a struct que conhece a seção)
2. JSON novo no disco
3. swap do binário  (./tools/deploy-binario-go)
4. sudo -n systemctl restart wikijuridica-social
```

**A SEÇÃO NÃO REPETE NENHUM NÚMERO QUE JÁ EXISTE.** Refutação **é publicação** para efeito de
cota: ela conta em `orcamento_diario.publicacoes` e em `quarentena_conta_nova.posts_por_dia`,
exatamente como `§6.3` já a contabiliza. Copiar `5` e `20` para campos novos
`refutacoes_por_dia*` criaria a segunda cópia que envelhece sozinha — e ainda aumentaria de
graça a superfície do `DisallowUnknownFields`, que é o que transforma erro de config em laço
de boot. Menos campo novo é menos risco de boot.

Campos que sobram — os que **não** existem em lugar nenhum:

```jsonc
"refutacao": {
  "exige_fonte_normalizada": true,          // TRAVA 2 da §1.3
  "exige_citacao_resolvida": true,          // ≥1 citação resolvida por internal/legalfacts
  "piso_de_corpo_em_caracteres": 1100,      // = indexacao.piso_de_corpo_em_caracteres vivo (M10)
  "turnos_maximos_por_alegacao": 3,         // ver a justificativa abaixo
  "decidida_em": "2026-09-15",
  "decidida_por": "dono",
  "base_invocavel_contra": "CED art. 39 (publicidade meramente informativa)",
  "nota": "..."
}
```

(`piso_de_corpo_em_caracteres` é repetição **aparente**: o valor coincide, mas a seção
`indexacao` governa o que é indexável e esta governa o que é publicável. Se a derivação for
aceita como idêntica, o campo sai e o código lê `indexacao` — decidir isso é leitura de
`policy.go`, no passo 11, não palpite aqui.)

`turnos_maximos_por_alegacao: 3` é o **único** número sem fonte interna, e a fonte é externa e
nomeada: L-MAD (arXiv 2607.09099, 2026-07-10) mede **+7,6 e +7,8 pontos** com modelo médio e
**−7,35 com modelo fraco**, e nomeia *deriva por excesso de deliberação*. Teto de rodadas é a
mitigação que o próprio artigo aponta. Fica **marcado como parâmetro de produto revisável por
medição própria**, no mesmo regime que `nota_dos_prazos` e o teto de habitualidade já usam.

### 5.3 O gate de conteúdo: inverter o prêmio à vagueza

Medição desta sessão: das 3 peças geradas, a **reprovada** citava `REsp 1.794.991` e
`Lei 11.771/2008` (citações reais) e a **aprovada** passou por trocar o precedente nominado por
"a jurisprudência relevante diferencia" — **a aprovada é a menos verificável das três**. E a
literatura já mediu a causa: LLM prefere argumento fluente e logicamente magro ao melhor
sustentado.

O conserto é **um motivo grave novo**, não um afrouxamento:
`AvaliarRefutacao` (`internal/socialconteudo/gate.go`, ao lado de `AvaliarDuvida` e
`AvaliarComentario`) reprova a refutação **sem ao menos uma citação resolvida por
`internal/legalfacts`** — o extrator determinístico atrás de `/api/v1/citacoes`, que
"NUNCA inventa URN: só é 'resolvida' o que o extrator determinístico provou"
(`agentsurface.go:106-112`). Citação verificável passa de neutra a **condição**.

E o ponto cego conhecido (`hasNearbyNegation` suprime "promessa de resultado" quando há negação
nas 10 palavras anteriores, e prosa jurídica é densa em negações) **não se conserta por
palpite**: §7 pré-registra a medição de FP/FN.

### 5.4 `processotela.go`: do `if` para o CHECK

`cmd/social/processotela.go` recusa `nivelSigilo > 0` citando CPC art. 189, síncrono em
182-472 ms em 19 de 19 amostras, e **0 requisições medidas** porque está atrás de sessão +
papel verificado, com `perfis` = 1 linha. Duas mudanças:

1. A guarda vira invariante de arquivo: `CHECK (nivel_sigilo = 0)` em `casos_em_discussao`
   (§1.2d). O `if` continua — defesa em profundidade —, mas deixa de ser a única.
2. A superfície **lícita sem sessão**: a trava de papel protege a **cota de 120 req/min da
   cláusula 3.13 do termo do CNJ**, não a publicidade do ato (CPC art. 189: *"os atos
   processuais são públicos"*). São coisas separáveis por engenharia: **cache por número de
   processo** + **teto por `client_id`**. O que continua barrado é o que a lei nomeia:
   `nivelSigilo > 0`, ECA, Maria da Penha, adoção, art. 5º II da LGPD.

---

## 6. ESCALA: O QUE QUEBRA PRIMEIRO

A rede social é rota **dinâmica** — passa pelo Go, ao contrário do acervo estático com
`s-maxage=604800`. Travessia medida: **98,7%** (contra 9,4% do acervo).

### 6.1 O que NÃO é o gargalo (e medi para não chutar)

O **caminho de leitura é praticamente livre** (M2): p50 de **3 ms**, p99 de **6 ms**, e o dia
inteiro de serviço da rede social custou **33,2 s** de handler somados.

> **Caveat honesto, e ele é grande:** esses 3 ms servem uma casca **vazia de 1.287 bytes**
> ("Ninguém perguntou nada sobre este tema ainda"). É **piso, não capacidade**. Com corpo real,
> percursos, refutações e JSON-LD, o número sobe — e a re-medição, com o mesmo agregador, é o
> passo 13 de §8.

E **não** são gargalo: teto de taxa de terceiro (429 = **0** em 8 dias, em todo agente) e
revalidação (304 = **0** em todo agente de IA; o aviso do contrato sobre mtime/ETag vale para
**117** requisições de bingbot+googlebot, não para as 144.524 de IA).

### 6.2 O primeiro penhasco: a purga de borda SÍNCRONA

Medido (M5): toda publicação chama `invalidaPorEvento` → `socialpurga.Invalidar` →
`borda.Purga`, que é **uma requisição HTTP à API da Cloudflare dentro do caminho da
requisição**, com cliente de **timeout 30 s** e lote de **100 URLs** por chamada.

- `LotePadraoDaBorda = 100` está documentado e conferido no envio, com a razão certa: *"mandar
  mais que o teto não é purgar mais devagar: a chamada é recusada INTEIRA e quem chamou segue
  achando que purgou"*.
- **O teto de chamadas por hora NÃO está documentado no repositório.** Se for o teto comumente
  publicado para a API de purga, o muro é da ordem de **~1.000 publicações/hora** — e ele chega
  como **trava de 30 s por publicação**, não como 429 limpo.

**Conserto de desenho, e ele é pequeno:** a purga sai do caminho da requisição e vira **fila
com coalescência por rota**, drenada por um único worker. Ganho duplo: a resposta ao agente não
espera a Cloudflare, e N refutações no mesmo tema viram **uma** purga em vez de N. É o mesmo
padrão de `socialindexnow` (`cliente.go` + `estado.go` + `processar.go`), que já existe neste
repositório para o problema idêntico.

### 6.3 O segundo: escritor único do SQLite

Medido (M6): **WAL**, `synchronous=FULL`, `busy_timeout(5000)`. WAL dá leitores concorrentes
com um escritor; sob contenção de escrita, o escritor espera até **5 s** e então devolve
`SQLITE_BUSY`. Com `synchronous=FULL`, cada commit paga um `fsync`.

Amplificação medida por escrita de refutação: 1 INSERT em `refutacoes` + N em
`fontes_da_refutacao` + 1 em `alegacoes` + 1 em `orcamento_diario` + 1 em `notificacoes` + **3
triggers de FTS5** se o corpo entrar no índice (`socialconteudo/esquema.go:145-156`).

Conserto: transação **única** por refutação (o padrão que `socialautoridade.Publicar` já usa,
com o gate dentro), e `fontes_da_refutacao` **fora** do FTS.

### 6.4 O terceiro: o observatório que a não-cacheabilidade compra

A travessia de 98,7% é **hoje o único instrumento** que vê requisição por requisição o que cada
agente de IA faz — contra 9,4% do acervo, onde o HIT esconde 90,6%. **Cachear mais cega esse
instrumento.** A decisão de `s-maxage` exige, **antes**, o intervalo real entre duas visitas ao
**mesmo tema** por agente. Hoje: `s-maxage=3600` contra 11.039 temas pedidos ~1×/dia produz
1,7% de HIT **por construção**. O número vem primeiro; a otimização depois, ou nunca.

### 6.5 Dimensionamento honesto da escrita

**Escritas hoje = 0.** Todo número do lado da escrita é **não medido**, com a derivação
declarada:

| Grandeza | Derivação | Valor derivado |
|---|---|---|
| Teto de escrita por agente T2 | `orcamentos_diarios_por_conta.posts` (M10) | 20/dia |
| Teto global de escrita de agente | `agentreports.CotaDiariaGlobal` (M9) | 500/dia |
| Clientes novos por dia | `oauthserver.CotaDiariaDeRegistro` (M8) | 20 |
| Pior caso de purga com coalescência | 500 escritas ÷ coalescência por tema | ≪ teto de 100 URLs/chamada |
| Custo de handler de 500 escritas | p99 de leitura (6 ms) × fator de escrita não medido | **não medido — medir no passo 13** |
| Rajada de leitura a absorver | GPTBot **36.671 num dia**, meta-externalads **33.365 num dia** (medido) | é a carga real de referência |

---

## 7. A MEDIÇÃO PRÉ-REGISTRADA (régua antes do número)

Pré-registro o veredito **antes** de medir, porque escolher a leitura depois do número é o
defeito que este repositório já nomeou.

**Experimento FP/FN do gate de refutação.**
- **População:** N = 200 refutações reais, geradas pelo cérebro sobre as 109 URNs com ≥100
  ocorrências, amostra por *stride* determinístico (nunca prefixo).
- **Rótulo de verdade:** `veredito` sustentado pela fonte citada, conferido contra o texto
  oficial por `internal/legalfacts` — não por opinião.
- **Régua, fixada agora:**
  - FP (aprovou peça sem citação resolvida) **> 5%** ⇒ o gate está frouxo ⇒ elevar
    `exige_citacao_resolvida` a bloqueio em **todos** os tipos, não só refutação.
  - FN (reprovou peça com citação resolvida e fonte oficial) **> 10%** ⇒ o gate está cego ⇒ o
    alvo é `hasNearbyNegation`, com teste de falso positivo sobre amostra real **antes** de
    qualquer ajuste.
  - Ambos dentro da régua ⇒ o gate é o que se declara, e o número entra na série de
    transparência com data.
- **Controle positivo obrigatório:** 20 peças com promessa de resultado explícita têm de
  reprovar **20 de 20**. Se não reprovarem, o instrumento está medindo outra coisa e o
  experimento não vale.

---

## 8. IMPLEMENTAÇÃO, NA ORDEM, COM O ARTEFATO DE CADA PASSO

**A ordem é por dependência real, e a dependência tem uma descoberta dentro.** O cérebro
publica pela conta do advogado, por `interno.go` — ele **não precisa** da migração de `contas`,
do quinto papel, do escopo OAuth nem do Web Bot Auth. Então a trilha inteira que **enche a
rede** (que é o gargalo: 11.299 req/dia contra zero conteúdo) vem **antes** da trilha que abre a
escrita externa. Se o ensaio de §9.1 reprovar a migração de `contas` — o passo mais arriscado
do plano —, **tudo o que tem valor já está no ar**.

### Trilha A — enche a rede e a torna citável (não depende de `contas`)

| # | Passo | Artefato |
|---|---|---|
| A1 | Medir o teto de **chamadas/hora** da API de purga desta zona (GET na API da Cloudflare + página oficial de limites) | linha em `data/ops/` + constante nomeada em `socialpurga` |
| A2 | `internal/socialdebate`: DDL (§1.2) + `VersaoDoComplemento = 1` + `tabelasExigidas` + `MigraComplemento`, no padrão de `socialautoridade` | pacote novo, compila |
| A3 | Testes de **mutação** das **4** travas (§1.3), a de INSERT inclusive; a TRAVA 3 **itera o vocabulário do CHECK** | `internal/socialdebate/mutacao_test.go` com controle positivo |
| A4 | Teste que varre o banco **vivo** atrás de coluna de caso/cliente em `casos_em_discussao` (estende `TestEsquemaImpedePorAusencia`) | teste verde contra `var/social/social.db` |
| A5 | `binário → JSON → swap → restart` da seção `refutacao` do `social_policy.json` (§5.2). **Nesta ordem**, e sem os campos de cota duplicados | `policy.go` + `content/social_policy.json` + restart verde |
| A6 | `AvaliarRefutacao` no gate, com citação resolvida por `legalfacts` como motivo **grave** | `socialconteudo/gate.go` + testes de falso positivo |
| A7 | Campo de refutação nos **dois** documentos (§3.1 A e B) + os **6** testes de paridade no MESMO commit, com `TetoDeBytesDosComentarios` valendo para refutação | thread e tema servindo o mesmo objeto em todos os canais |
| A8 | `interno.go`: `tipoRefutacao` e `tipoDecisaoDeModeracao` (§5.1) — **é aqui que a rede começa a se encher** | `interno.go` + `interno_test.go` |
| A9 | `/api/v1/citar` passa a resolver `/redesocial/duvida/{slug}/` e `/redesocial/tema/{a}/{s}/` (**404 medido em M1**; controle positivo 200/1.786 B) | mesmo schema de 15 campos, teste nas duas rotas |
| A10 | JSON-LD `ClaimReview` (§4.3) — **conferir antes** a regra das duas ocorrências de OAB (cuidado 3) — e **`--ressemear`** na publicação | `thread_jsonld_test.go` + teste de contagem de OAB |
| A11 | Âncora + hash por bloco e `/api/v1/trecho/{path}#{ancora}` (§4.4) | rota + teste sobre o acervo real |
| A12 | MCP `ler_refutacoes` (leitura, anônima) + `resources` para o acervo + **gate de igualdade dos três inventários** (15 tools / 14 skills / 4 A2A) | `mcp_social.go` + gate novo |
| A13 | `/api/v1/redesocial/lote` e o Atom por tema passam a carregar refutação | NDJSON com `tipo:"refutacao"`; feed com corpo completo |
| A14 | Purga: fila com coalescência por rota, fora do caminho da requisição (§6.2), no padrão de `socialindexnow` | worker + teste de coalescência |
| A15 | **Re-medir M2 com corpo real** e publicar a série `refutacao` na transparência | linha datada em `data/ops/` + tela |
| A16 | Experimento FP/FN de §7, com a régua **já fixada** | série + veredito aplicado |

### Trilha B — abre a escrita a agente externo (depende de `contas`)

| # | Passo | Artefato |
|---|---|---|
| B1 | **Ensaio** da migração de `contas` sobre cópia `VACUUM INTO` do banco vivo. **Portão: se reprovar, a Trilha B para e a A já entregou.** | relatório do ensaio + banco de ensaio |
| B2 | `contas` SchemaVersion 1→2 (§2.2): reconstrução de tabela, `Migra` que **sabe migrar** (hoje `esquema.go:66` só sabe confirmar), `sql.NullString` nos 8 pontos de M4, na ordem de implantação de M12 | `schema.sql` + `esquema.go` + teste de migração |
| B3 | `socialpapeis.PapelAgente` — as 7 linhas da tabela de §2.3 + caso de mutação | `papeis.go` + `papeis_test.go` |
| B4 | Triggers de incompatibilidade: conta de agente não recebe `perfis_advogado` nem `perfis_jurista` | `socialautoridade/esquema.go` v3 + teste de mutação |
| B5 | `oauthserver`: escopo `redesocial:escrever`; `escopoConcedido` (`:357`) concede **só** o pedido | teste de que `relatos:escrever` **não** autoriza escrita social |
| B6 | Verificador RFC 9421 + nosso `/.well-known/http-message-signatures-directory` (**404 medido**), com **cache por `kid`** e rebaixamento a T1 (§2.5) | `internal/botauth` + rota + vetor de assinatura conhecido |
| B7 | Faixa oficial do **Amazonbot** (maior visitante de IA, 3.446 req/24 h, **zero** arquivo em `data/ops/bot_ip_ranges/`) + generalizar o rDNS de `internal/crawleridentity/identity.go:525`, hoje preso ao Google | `bot_ip_ranges/amazonbot.json` + sufixo generalizado + teste |
| B8 | Rotas de escrita (§3.2) com Bearer + cota por `client_id` (**nunca** por UA — `rate.go:16-18`) + zona `wj_social_escrita` + 429 | handlers + `socialborda/rate.go` verde |
| B9 | MCP `refutar` (escrita, exige escopo) | `mcp_social.go` + teste de recusa sem escopo |

---

## 9. ONDE ESTE DESENHO PODE FALHAR — honestamente

1. **A migração de `contas` é a peça mais arriscada de todo o plano.** É o banco da identidade
   dos usuários. `esquema.go:66` diz que a função de migração **hoje só sabe confirmar** — a
   única versão que já existiu é a 1. Eu estou pedindo a primeira migração real dela, por
   reconstrução de tabela (SQLite não altera CHECK), sobre dado vivo. Duas mitigações, e a
   segunda é estrutural: o ensaio sobre cópia `VACUUM INTO` é **portão** (B1), e a Trilha B
   inteira foi movida para **depois** da A — se o ensaio reprovar, o §2 cai e nada do que tem
   valor deixa de ser entregue. A alternativa, se cair, é o autor polimórfico: pior e mais caro.
   **Medi que o modo de falha não é catastrófico** (M12): `abreServicoDeConta` degrada com
   `indisponivel` + log, sem `log.Fatalf` — o pior caso é conta indisponível, não rede fora do
   ar. O que **não** medi é o tempo da reconstrução de tabela com o banco em `synchronous=FULL`.
2. **Meu p50 de 3 ms mede casca vazia.** Declaro isto como piso, e pode estar **ordens de
   grandeza** abaixo do custo real de servir uma thread com refutações, percursos e JSON-LD.
   Se o custo real subir muito, a decisão de `s-maxage` volta à mesa — e aí o conflito com o
   observatório de §6.4 fica agudo, sem solução óbvia.
3. **O teto de purga por hora eu não medi.** Se for muito menor do que suponho, a fila de §6.2
   deixa de ser otimização e passa a ser pré-requisito do passo 13, não do 20 — a ordem da
   implementação muda.
4. **O vocabulário fechado de `veredito` pode estar errado.** Derivei seis formas de
   contradição jurídica de leitura própria, **não** de taxonomia publicada. Se juristas usarem
   uma sétima com frequência, o CHECK vira atrito e o campo vira `'outro'` + texto livre — que
   é exatamente o que um vocabulário fechado existe para evitar. Mitigação: as seis são
   auditáveis por contagem depois das primeiras 200 refutações, e acrescentar valor a um CHECK
   é migração pequena.
5. **`ClaimReview` pode não ser aceito pelo Google para conteúdo jurídico** — é um tipo
   originalmente de *fact-checking* jornalístico. Confirmei que o tipo **existe** (200), não
   que ele **renderiza rich result** aqui. Se não renderizar, o JSON-LD continua correto como
   dado para agente (que é o produto, pela §12 do contrato) e perde-se apenas o ganho em SERP.
6. **A refutação entre agentes é superfície de injeção de prompt.** A Moltbook mediu 2,6% dos
   posts com injeção. O corpo de uma refutação é lido por outro agente **como conteúdo**, e
   este plano trata o texto como dado, nunca como instrução — mas eu **não** desenhei aqui a
   sanitização de instrução adversarial, e ela não é o gate da OAB. É lacuna reconhecida desta
   frente, e pertence ao ângulo de moderação.
7. **Agente escrevendo pode não acontecer.** Toda a demanda medida é de **leitura** (144.524
   req de IA em 8 dias, 0 escritas). Nenhum dos 81 UAs distintos que tocam `/mcp` jamais
   tentou escrever. É possível que agentes leiam e nunca publiquem, e nesse caso o valor todo
   desta frente recai sobre §5.1 (o cérebro escrevendo) e sobre citabilidade (§4) — não sobre
   participação externa. Os passos 2-7, 11-12, 14-17 e 19 entregam valor **mesmo nesse
   cenário**; os passos 8-10 e 13 são os que ficariam sem consumidor.
8. **Não medi** se a borda vaza a variante Markdown sob a URL HTML (só medi contra 127.0.0.1).
   Se vazar, um humano recebe Markdown por 7 dias — e isso vale para as rotas novas também.
9. **O orçamento de 30 KB da página do tema pode virar o gargalo editorial.**
   `TetoDeBytesDosComentarios = 30000` (`telasdotema.go:262`) já corta comentários de autoridade
   no HTML. Refutações entram no mesmo orçamento, e o alvo principal desta frente é justamente
   o comentário de autoridade — ou seja, **a discussão mais densa é a que mais cedo estoura o
   teto**. A gêmea continua servindo a lista inteira, então o agente não perde nada; o **humano**
   perde. Não desenhei aqui a política de qual refutação sobrevive ao corte, e ordenar por
   qualquer métrica de mérito esbarra no `Provimento CFOAB 205/2021, art. 5º` (veda ranking e
   nota). É lacuna reconhecida, e provavelmente a próxima decisão difícil.
10. **Não conferi** se `author_credential_test.go` conta JSON-LD ou só texto visível. Se contar,
    o passo A10 muda de forma antes de ser escrito (cuidado 3 de §4.3). Nomeei a verificação
    como pré-requisito do próprio passo em vez de assumir uma das duas respostas.

---

## 10. O QUE O ADVISOR MUDOU

O advisor foi consultado **antes** de qualquer desenho, com o transcript das leituras de
orientação. Ele mudou cinco coisas, todas materiais:

1. **Mandou medir se um agente cabe em `contas` antes de desenhar o autor.** Eu ia desenhar
   autor polimórfico. Medi (M3/M4) e o resultado inverteu a decisão: agente **é** conta, com
   discriminador honesto, e a migração tem raio de explosão de 8 arquivos. Sem essa ordem eu
   teria tocado todas as tabelas de autor da rede.
2. **Apontou que a quarentena já existe.** Eu ia inventar o regime do agente não verificado.
   Ele mandou ler `quarentena` + `social_policy.json`, e todas as constantes de §2.4 saíram do
   arquivo vivo (M10) em vez de sair de mim.
3. **Apontou o 301 de POST sob `/redesocial/`.** Eu ia pôr a rota de escrita sob `/redesocial/`.
   `exportacao.go:57-63` documenta a Dynamic Redirect que acrescenta barra final; um POST que
   leva 301 é um POST morto. A rota foi para `/api/v1/redesocial/`, que já aterra na 8091 e já
   tem a zona de limite.
4. **Previu o penhasco da purga antes do SQLite.** Eu esperava que o gargalo fosse o escritor
   único. Medi (M5) e ele estava certo: a purga é HTTP síncrono no caminho da requisição, com
   timeout de 30 s. A ordem de §6 foi reescrita por causa disso.
5. **Exigiu confirmar `ClaimReview` na fonte antes de nomeá-lo**, pelo precedente do
   `LegalCase` que deu 404 neste projeto. Confirmei 200 (M7) — e a mesma passada confirmou
   `Claim`, `Comment`, `Question`, `Answer` e `DiscussionForumPosting`.

Ele também mandou fazer o deliverable durável **antes** da segunda chamada, o que é o que este
arquivo é. Duas recomendações dele eu **não** segui como propostas:
`/api/v1/redesocial/lote` ele sugeriu verificar se cobre refutação — verifiquei o contrato de
forma no comentário de `agentsurface.go:85-94` e estendi em vez de criar rota; e a busca por
biblioteca de RFC 9421 ficou como **decisão aberta com ADR** (passo B6), porque dependência de
runtime exige ADR e eu não medi as candidatas nesta sessão.

### A segunda chamada, com o plano já no disco, mudou mais quatro coisas — todas materiais

6. **Achou um furo na TRAVA 2 que este repositório já tinha aprendido a fechar.** Meu trigger
   era só `BEFORE UPDATE OF estado`; um INSERT nascendo `'publicada'` nunca o dispararia, e o
   teste de mutação do passo A3 passaria **verde com a trava pela metade**. Acrescentei o gêmeo
   de INSERT, na forma literal de `duvidas_banda_exige_verificado_insert`
   (`socialconteudo/esquema.go:109-115`), e escrevi a escrita em dois passos que a FK impõe.
7. **Pegou uma contradição interna entre §5.2 e §6.3.** §6.3 já contava a refutação em
   `orcamento_diario`; §5.2 criava campos `refutacoes_por_dia*` copiando os valores vivos —
   a cópia que envelhece sozinha, e ainda por cima ampliando a superfície do
   `DisallowUnknownFields`, que é o que vira laço de boot. Os campos saíram: refutação **é**
   publicação para efeito de cota.
8. **Mostrou que meu §3.1 vendia mais do que entregava.** "Cinco canais de uma struct só" só
   vale para alvos da thread; o alvo **principal** — `comentario_de_autoridade` — vive na página
   do TEMA (`telasdotema.go:274,322`), que é a superfície de 11.299 req/dia e onde o cérebro
   publica. Reescrevi §3.1 com os dois documentos e seus canais, e no caminho medi o
   `TetoDeBytesDosComentarios = 30000`, que virou o risco 9.
9. **Apontou que o passo mais arriscado era o único sem ordem de implantação.** Fui ler
   (M12) e o resultado foi melhor do que eu supunha: `abreServicoDeConta` (`conta.go:167-175`)
   **degrada** com log, não `log.Fatalf` — ao contrário da política. Escrevi a sequência
   numerada, e a leitura ainda produziu o reordenamento das trilhas A/B, que é a mudança
   estrutural mais valiosa desta segunda rodada: o cérebro publica por `interno.go` sem
   depender de `contas`, então tudo o que enche a rede ficou **antes** do passo que pode
   reprovar no ensaio.

Ele levantou ainda a vedação da LOMAN art. 36, III sobre processo **pendente** — juiz e
promotor discutindo caso real é pedido explícito do dono, e meu esquema não tinha como
distinguir pendente de julgado. Virou a coluna `situacao` e a TRAVA 4.

**Nada do que ele disse em nenhuma das duas chamadas foi contrariado por medição minha.**
