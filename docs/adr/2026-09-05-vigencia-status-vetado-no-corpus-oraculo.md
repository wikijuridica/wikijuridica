# ADR: o corpus-oráculo ganha o estado de vigência `vetado`

Date: 2026-09-05

## Decision

`internal/corpus` passa a aceitar um sexto estado em `OracleRecord.VigenciaStatus`:

```go
VigenciaStatusVetado = "vetado"
```

Ele descreve o dispositivo que o **veto presidencial derrubou antes da
promulgação** — o texto nunca produziu efeito. A invariante é tão importante
quanto o rótulo: um registro `vetado` tem `vigencia_inicio`, `vigencia_fim` e
`revogado_por` **vazios**, e `statusCanCoverDate` o recusa, de modo que
`Get`/`ResolveAsOf`/`ResolveURNAsOf` nunca o devolvem como redação aplicável a
data alguma.

Três elos mudam junto:

1. **Modelo** (`internal/corpus/corpus.go`) — a constante, a invariante em
   `validateRecord` (que roda no `Put` **e** na reabertura do manifest), a
   recusa em `statusCanCoverDate` e um ramo estreito em `validateCorrection`
   (`validateVetoCorrection`) para a única transição de estado jurídico que não
   carrega data.
2. **Produtor** (`cmd/collect-oracle/run.go`, ramo (2b) de `putVersionedParts`)
   — passa a **gravar** o estado, reusando a mesma `version_seq` e o mesmo blob,
   em vez de apenas relatar.
3. **Detector** (`internal/sourcesnapshotaudit/audit.go`) — aceita `vetado` como
   `vigencia_status` válido e reconhece a cabeça de veto declarada como cadeia
   fechada legítima, sem parar de acusar o defeito verdadeiro.

## Context

O modelo de vigência não sabia representar uma norma que nunca entrou em vigor.
Dois agentes pararam nesse ponto pedindo ADR, e o comentário de
`cmd/collect-oracle/revogacao.go` registrava a lacuna por escrito: *"não existe
hoje um VigenciaStatus para 'nunca entrou em vigor' em internal/corpus"*.

Consequência: um dispositivo vetado era forçado num estado que mente sobre ele.
Num acervo jurídico, **afirmar vigência errada é a classe de erro mais cara que
existe** — e é a mesma família do defeito das 121 cabeças revogadas gravadas
como vigentes, que a política de revogação datada corrigiu em 2026-09-04.

Por que nenhum dos cinco estados existentes serve:

| estado | por que não descreve o veto |
|---|---|
| `revogado` | o revogado **vigorou** e cessou: tem janela real e ato revogador a citar |
| `nao_vigente_ainda` | esse **vai** entrar em vigor numa data futura; o vetado não vai nunca |
| `suspenso` / `alterado` | ambos pressupõem eficácia prévia |
| `nao_verificado` | é estado **epistêmico** ("a fonte não prova a janela"); o veto é estado **jurídico**, provado pela consolidação oficial, que imprime `(VETADO)` no lugar do artigo |

`vetado` é o rótulo que a fonte oficial literalmente usa, e por isso o único
honesto.

## Evidence

Censo *read-only* sobre `data/source-snapshots/manifest.jsonl` (9.037 linhas,
6.675 séries), reproduzindo a classificação de
`sourcesnapshotaudit.inspectDevice` sobre o blob autenticado da cabeça canônica
de cada série — 2026-09-05:

- **37 cabeças** cujo blob é um marcador oficial de veto;
- **37 de 37** gravadas com `vigencia_status: "vigente"`;
- **37 de 37** com `vigencia_fim` vazio e `vigencia_inicio` **preenchido com a
  data do diploma**;
- **37 de 37** com `revogado_por` vazio;
- **0** com hash divergente do blob;
- partição por corpo: **27 integrais** + **10 contaminados** por falha de
  segmentação — exatamente os dois tetos que
  `known_issue_ceiling_test.go` registra (`source_snapshot_veto_integral_placeholder=27`,
  `source_snapshot_veto_marker_contaminated=10`).

Amostras (URN, dispositivo, status, `vigencia_inicio`, corpo):

```
decreto.lei:1943-05-01;5452  art_390-A  vigente  1943-05-01  (VETADO na Lei nº 9.799, de 26/5/1999)
decreto.lei:1943-05-01;5452  art_401-B  vigente  1943-05-01  (VETADO na Lei nº 9.799, de 26/5/1999) CAPÍTULO IV ...
lei:1990-09-11;8078          art_108    vigente  1990-09-11  (VETADO). TÍTULO VI DISPOSIÇÕES FINAIS
lei:1990-09-11;8078          art_109    vigente  1990-09-11  (VETADO).
```

Ou seja: o corpus afirmava que o art. 108 do CDC vige desde 1990-09-11 e que os
arts. 390-A/401-A da CLT vigem desde 1943-05-01, quando o veto derrubou os três
antes da promulgação.

Distribuição por canal das 37 cabeças (define a recoleta):

| canal | integrais | contaminadas | total | URNs |
|---|---|---|---|---|
| `camara_legin_html` | 18 | 8 | **26** | CLT (4), CDC (13), Código Civil (2), LGPD (7) |
| `normas_leg_br_api_publica_texto` | 9 | 2 | **11** | Lei 8.213 (5), Lei 8.245 (2), Lei 9.099 (1), CPC/2015 (3) |

Os dois canais passam pela mesma reconciliação (`putVersionedSet` com
`revogacoesDoTextoBruto`: `run.go:527` e `normas.go:210`), então o código dos
dois corrige. **Mas só um dos dois pode rodar hoje** — ver a seção de recoleta.

## O que NÃO muda: por que o veto não fecha vigência com data

`detectaVetoDispositivo` nunca devolve data, e isso é deliberado. A data que às
vezes acompanha o marcador (`(VETADO na Lei nº 9.799, de 26/5/1999)`) é a data
em que **outra** lei inseriu redação equivalente — não é a data em que este
dispositivo deixou de valer, porque ele nunca valeu. Gravar
`vigencia_fim = essa data` afirmaria uma vigência (1943-05-01 → 1999-05-26, no
caso da CLT) que **nenhuma fonte declara**: seria o mesmo erro da revogação
fechada com a data da observação, só que na direção contrária.

Por isso a correção limpa `vigencia_inicio` em vez de preencher `vigencia_fim`.
Uma vigência que nunca começou não tem início.

## Por que `validateCorrection` ganhou uma exceção

A regra geral do store é: **toda correção que muda o estado jurídico fecha a
linha com um `vigencia_fim`**. Cumpri-la para o veto obrigaria a inventar uma
data. `validateVetoCorrection` é a exceção estreita, e ela prova campo a campo
que não está apagando vigência observada:

- `previous.vigencia_fim` tem de estar **vazio** (linha já fechada com data
  descreve vigência observada; marcá-la como vetada apagaria a observação);
- `candidate.vigencia_fim`, `candidate.vigencia_inicio` e `revogado_por` têm de
  estar **vazios**;
- todo o resto — hash, `blob_ref`, canal, URL, `version_seq`, eixo — permanece
  imutável;
- a observação (`last_verified_at`, `as_of_date`, `fetched_at`) só pode avançar.

Segurança para o acervo existente: **zero** das 9.037 linhas tem
`vigencia_status: "vetado"` hoje, portanto reabrir o manifest de produção nunca
passa pelo ramo novo.

## Como isto não vira afrouxamento

O detector deixar de acusar a cabeça vetada declarada só é correção enquanto o
rótulo continuar preso à evidência. Três controles seguem reprovando, e cada um
tem teste que falha se ele for removido:

1. **`source_snapshot_veto_marker_contaminated` é incondicional.**
   Contaminação é defeito de **segmentação** — o blob carrega o heading seguinte
   (`(VETADO). TÍTULO VI DISPOSIÇÕES FINAIS`, art. 108 do CDC). Declarar o veto
   não recorta o texto. As 10 cabeças contaminadas continuam vermelhas.
2. **`source_snapshot_veto_integral_placeholder` continua acusando** toda cabeça
   de veto que o produtor ainda declare `vigente`, `nao_verificado` ou
   `nao_vigente_ainda`. É o defeito real medido — as 27 de hoje.
3. **Duas guardas simétricas novas**, com teto zero:
   `source_snapshot_vetado_status_without_veto_marker` (rótulo `vetado` sobre
   corpo que não é marcador de veto) e
   `source_snapshot_vetado_status_with_vigencia_window` (rótulo `vetado` com
   início, fim ou ato revogador). Sem elas, `vetado` viraria a palavra mágica que
   silencia acusação.

O estado do dispositivo é decidido pelo **blob autenticado**, não pelo manifest:
a classificação em `audit.go` não consulta `internal/corpus` (só `guard.go` o
importa, para abrir a vista guardada) e re-deriva a invariante por conta
própria. Um afrouxamento no produtor não vira verde no auditor.

## Consequences

- **O número do gate `source-snapshot-corpus` NÃO cai com esta mudança**, e isso
  é esperado. Medido depois da alteração, o gate devolve as mesmas 13 categorias
  com as mesmas contagens de 2026-09-05, incluindo `veto_integral_placeholder=27`
  e `veto_marker_contaminated=10`. A queda exige **recoleta ao vivo** (rede +
  escrita em `data/source-snapshots/`), porque é a recoleta que executa o ramo
  (2b) e grava o estado. `known_issue_ceiling_test` segura o teto e continua
  vermelho até lá. Verificado depois da mudança: `veto_integral_placeholder=27`,
  `veto_marker_contaminated=10`, `repair_candidates=283`, e nenhuma das 13
  categorias abaixo do teto (o teste roda com `-v` e não emite uma única linha
  `melhorou`).
- Uma vez gravado o estado, a série sai de `OpenObservedDispositivosForUpdate`
  (que só devolve `vigente`/`nao_verificado`) e a correção é **idempotente**:
  recoletas seguintes não a tocam.
- Cabeça vetada que volte a ter texto substantivo (re-inserção por outra lei)
  não abre redação nova nem aborta o documento: cai no ramo de **conflito de
  estado legado que já existia** (`statusConflitoEstadoLegado`), é pulada e
  contada. Nenhum código novo foi preciso para isso — uma versão anterior desta
  correção acrescentava um ramo próprio em `planVersioned`, e a medição mostrou
  que ele era inalcançável a partir das duas únicas formas de `base` que o
  produtor emite (`nao_verificado` sempre, `revogado` quando o preâmbulo
  declara). O ramo foi removido em vez de mantido como código morto.
- Cabeça que já cite ato revogador não é marcada como vetada — apagar a citação
  verbatim destruiria proveniência. Fica intacta, contada em
  `VetoConflitoExigeRevisao` para decisão jurídica.
- **Lacuna declarada, não corrigida:** `vetoedPrefixRE` (auditor) aceita `[` e
  marcador sem parêntese; `reMarcadorVeto` (produtor) exige parêntese. Um
  dispositivo que o auditor classifique como veto mas o produtor não reconheça
  continuará acusado depois da recoleta. Nenhuma ocorrência assim existe nas 37
  medidas hoje — os dois concordam nas 37 —, e alargar o regex do produtor sem
  amostra real seria heurística frouxa.
- Cabeças de veto com menos de 30 bytes continuam contadas em
  `source_snapshot_head_under_30_bytes`: é outra acusação, legítima e
  independente desta.

## Recoleta (fora do escopo de quem escreveu esta ADR)

A queda do número exige rede e escrita no corpus. Três medições feitas antes de
escrever esta seção mudam o comando em relação ao óbvio:

1. **`tools/run-recoleta-corpus-oraculo` não serve como está.** Ele fixa
   `--somente-vencidos`, e os quatro diplomas alvo **não estão vencidos hoje**.
   Medido em 2026-09-05 nas cabeças de norma inteira: `next_check_at` vazio e
   `last_verified_at` = 2026-07-17 (CLT, CDC, CC) / 2026-07-18 (LGPD). Com
   `cadenciaDiplomaEstavel = 60 dias` (`cadencia.go:31`), `vencidoDerivado`
   coloca a revisita em **2026-09-15/16**. Rodar o wrapper hoje imprime
   `already_current / nao_vencido_ate_derivado_de_2026-07-17` e **não corrige
   nada**.
2. **`--normas-fulltext` está fora do padrão por medição, e deve continuar
   fora.** O próprio wrapper registra o ensaio de 2026-09-04 numa cópia isolada:
   a varredura ampla desse canal levou o total de *issues* de **451 para 868**
   (`placeholder_head` 58 → 351, `device_heading_mismatch` 48 → 175) em troca de
   4 correções. As **11** cabeças de veto desse canal ficam onde estão até a
   segmentação do consolidado de normas.leg.br ser tratada. Trocar 11 correções
   por ~420 defeitos novos seria piorar o acervo.
3. **`go-modern` injeta `devcmds` sozinho** (`tools/go-modern:121-123`), e o
   pacote inteiro de `cmd/collect-oracle` tem essa tag. Não se passa `--` antes
   das flags: `go run` já entrega tudo depois do pacote ao programa.

O comando que corrige as **26 cabeças alcançáveis** é, portanto, o canal curado
da Câmara **sem** o filtro de cadência:

```bash
# ensaio sem rede primeiro
./tools/go-modern run ./cmd/collect-oracle --camara-legin --prepare-only

# recoleta real (rede + escrita em data/source-snapshots/)
./tools/go-modern run ./cmd/collect-oracle --camara-legin \
    --corpus-root data/source-snapshots --budget 25m

# passos 2 e 3 NÃO são opcionais: manifest novo com journal velho deixa
# EvaluateQuarantineCoverage sem cobertura e OpenGroundingStore falha fechado.
./tools/go-modern run ./cmd/plan-source-snapshot-repair \
    --root data/source-snapshots --journal data/source-snapshots/repair-journal.jsonl \
    --append --expected-journal-sha256 "sha256:$(sha256sum data/source-snapshots/repair-journal.jsonl | awk '{print $1}')"
./tools/go-modern run ./cmd/check source-snapshot-corpus
```

Alternativa equivalente e serializada sob o mesmo `flock`, se e quando os
diplomas vencerem (a partir de 2026-09-16):
`CANAIS="--camara-legin" tools/run-recoleta-corpus-oraculo`.

### Previsão falsificável do resultado

Depois da passada `--camara-legin`, e **só** dela:

| código | hoje | previsto | por quê |
|---|---|---|---|
| `source_snapshot_veto_integral_placeholder` | 27 | **9** | as 18 integrais da Câmara passam a declarar `vetado`; as 9 de normas.leg.br continuam |
| `source_snapshot_veto_marker_contaminated` | 10 | **10** | contaminação é defeito de segmentação, independe do estado declarado |

Se o número der diferente de 9, **a hipótese está errada e a correção precisa
ser reexaminada** — não é caso de ajustar o teto para o que veio.

O teto de `source_snapshot_veto_integral_placeholder` em
`internal/sourcesnapshotaudit/known_issue_ceiling_test.go` desce **no mesmo
commit** da recoleta, com o número medido. As 11 cabeças de normas.leg.br ficam
como dívida declarada, atrás da segmentação daquele canal.

## Alternativas rejeitadas

- **Reusar `nao_verificado`.** Confunde estado epistêmico com jurídico e apaga a
  informação: `nao_verificado` diz "não sei", e aqui a fonte oficial diz.
- **Reusar `revogado` com `vigencia_fim` = data do marcador.** Afirmaria uma
  janela de vigência que nenhuma fonte declara. É a mentira que motivou a ADR.
- **Manter o rótulo `vigente` e só filtrar no consumo.** Deixa a mentira gravada
  no manifest, que é a fonte de verdade auditável e a base de qualquer
  *grounding* futuro.
- **Manter `vigencia_inicio` no registro vetado.** "Vetado desde 1943-05-01" é
  autocontraditório; trocaria uma mentira por outra.
