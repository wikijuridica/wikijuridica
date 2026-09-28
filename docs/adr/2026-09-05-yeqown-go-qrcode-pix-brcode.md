# ADR: `yeqown/go-qrcode/v2` para desenhar o QR do BR Code do Pix

Data: 2026-09-05

## Decisão

Adotar `github.com/yeqown/go-qrcode/v2 v2.3.0` como dependência de runtime Go
**direta**, com versão fixada e escopo de importação de **um único diretório**:
`internal/pixqrcode/`.

A dependência entra por **uma** razão: a correção de erro Reed-Solomon sobre
GF(2^8) do QR Code — polinômio gerador por versão e nível, segmentação em blocos
de dados e paridade, e escolha da máscara por pontuação, tudo definido na
ISO/IEC 18004. Isso é matemática de código corretor, não regra de negócio.

**O que continua construído em casa, e não muda:**

- o **payload do BR Code** permanece em `internal/pixbrcode` — cadeia TLV do
  padrão EMV-QRCPS adotado pelo Banco Central, com o CRC-16/CCITT-FALSE ancorado
  no vetor canônico do catálogo CRC RevEng (`0x29B1` para `"123456789"`);
- o **desenho da imagem** sai de `image/png` da biblioteca padrão do Go. Os
  writers de imagem do próprio módulo (`github.com/yeqown/go-qrcode/writer/...`)
  ficam de fora de propósito: arrastariam rasterização e fontes que este
  repositório não precisa. O escopo de importação de um diretório os exclui por
  construção, não por disciplina.

## Licença, lida na fonte oficial

| módulo | versão | licença | conferido em | onde |
|---|---|---|---|---|
| `github.com/yeqown/go-qrcode/v2` | `v2.3.0` | MIT | 2026-09-05 | LICENSE **dentro do zip publicado** (`sha256:65ed7f561093a926bcee235df0ba65449a86fdd67cf8aa3df92c96b55a0d4be7`), idêntico ao de `https://github.com/yeqown/go-qrcode/blob/main/LICENSE` |
| `github.com/yeqown/reedsolomon` | `v1.0.0` | MIT | 2026-09-05 | `https://github.com/yeqown/reedsolomon/blob/master/LICENSE` (`sha256:58fb0c85bfc183bad46c47dd38ac17e3372d86c1fcb65bce880fa1d964424f69`) |

**Ressalva registrada, e não escondida:** o zip publicado de
`github.com/yeqown/reedsolomon v1.0.0` **não contém arquivo LICENSE**. O
arquivo existe no repositório (`master`, MIT, "Copyright (c) 2026 yeqown"), mas
foi acrescentado depois da tag `v1.0.0`. Na prática isso significa que a versão
que este repositório compila não carrega o texto da licença junto — quem auditar
o `go.mod` sem ir ao repositório não a encontra. É uma pendência de
_upstream_, não um impedimento: o autor é o mesmo do `go-qrcode` (MIT) e a
licença declarada do repositório é MIT. Fica aqui escrito para que a próxima
auditoria de licença não confunda "não achei" com "não tem".

Ancoragem de integridade no `go.sum` (é ela que impede troca silenciosa de
conteúdo sob a mesma versão):

```
github.com/yeqown/go-qrcode/v2 v2.3.0 h1:MMsNJgZrG95g8SOGGGaGcEZkOt1ByHjeCLSaymGm9aY=
github.com/yeqown/reedsolomon v1.0.0 h1:x1h/Ej/uJnNu8jaX7GLHBWmZKCAWjEJTetkqaabr4B0=
```

## Vulnerabilidade conhecida, medida na árvore com a dependência dentro

`tools/generate-sca-govulncheck-evidence` rodou sobre `./internal/... ./cmd/...`
**depois** de o módulo entrar no `go.mod`, em 2026-09-05:

```
verdict=pass alcancaveis=0 so_no_grafo=3 escopo=./internal/... ./cmd/...
tool=v1.7.0 db=2026-09-02 19:12:04 +0000 UTC
```

A linha ficou em `data/ops/sca_govulncheck_evidence.jsonl`, com o SHA-256 do
`go.mod` e do `go.sum` que ela varreu — é esse par de hashes que o gate
`sca-govulncheck-evidence` confronta com a árvore do commit. Mexer de novo no
grafo de dependências **depois** deste commit exige nova varredura: evidência
que descreve uma árvore que não existe mais é o defeito que criou o gate
(BUG-056, três dias sem prova válida em 2026-08-26).

## Escopo permitido

- importação **exclusivamente** em `internal/pixqrcode/`;
- geração do símbolo e do PNG de uma cobrança Pix estática;
- evidência de escala em `data/ops/pix_qrcode_benchmark_evidence.jsonl`;
- **nenhum** acesso a `public/`, `content/pages.json`, `published_manifest`,
  sitemap ou `.release-staging`; `publication_allowed=false`,
  `render_allowed=false`, `sitemap_allowed=false` na evidência.

## Justificativa

O Manual de Padrões para Iniciação do Pix v2.10.0 do BCB (p. 14) é explícito:
a criação do QR Code estático **não** faz parte da API Pix. Ou seja, cobrar por
Pix estático não exige credencial, certificado mTLS, _onboarding_ em PSP nem
gateway de terceiro — exige montar corretamente uma cadeia TLV, fechar com
CRC-16 e desenhar um símbolo QR válido.

Os dois primeiros já existiam em `internal/pixbrcode`, testados contra vetor
canônico. O terceiro é o único ponto em que escrever do zero seria trabalho sem
benefício: reimplementar Reed-Solomon, as tabelas de blocos das 40 versões e a
pontuação de máscara produziria, na melhor hipótese, o mesmo símbolo — e, na
pior, um símbolo que a maioria dos leitores aceita e um banco específico recusa.

## Riscos e controles

**Risco principal: o símbolo carregar bytes que não são o payload.** É defeito
de caminho de dinheiro e não produz sintoma nenhum do nosso lado — a imagem sai
bonita e o aplicativo do pagador recusa, ou pior, lê uma chave que não é a
nossa.

O controle é a **volta obrigatória**: `internal/pixqrcode.MatrizDoTexto` não
devolve símbolo que ela mesma não tenha conseguido ler de volta. A leitura de
volta é **código desta casa** (`internal/pixqrcode/decodifica.go`), e não a
biblioteca relendo o que ela mesma escreveu — percorre a matriz no zigue-zague
do padrão, desfaz a máscara e remonta os bytes. A escolha da máscara sai por
eliminação: as oito do padrão são aplicadas e a leitura só é aceita quando UMA
única delas produz cadeia bem formada até o último byte de enchimento.

**Alcance dessa guarda, dito sem maquiagem:** ela prova que a **área de dados**
do símbolo contém, bit a bit, o payload do BR Code. Os módulos de **correção**
ficam fora — recalculá-los aqui seria desfazer a única razão de a biblioteca ter
sido adotada. O teste de mutação (`TestUmModuloTrocadoDerrubaALeitura`) inverte,
um a um, todos os módulos da área de dados e exige que a leitura caia em cada
um deles.

**Risco secundário: escapar do diretório.** Controlado pelo gate
`codex2-policy-enforcement`, que reprova importação fora de
`internal/pixqrcode/` com `codex2_policy_approved_dependency_import_scope_escape`,
e exige versão exata, ADR presente no disco e evidência sem sinalizador público.

**Risco de tabela:** a leitura de volta depende da coluna do nível M da tabela
de blocos (ISO/IEC 18004) e dos centros de padrão de alinhamento, transcritos
para as versões 1 a 16. Uma transcrição errada é acusada de imediato:
`Decodifica` confere que o percurso recolheu **exatamente** o número de módulos
que a versão comporta, e o teste percorre seis versões de estruturas diferentes
(bloco único, dois blocos, quatro blocos, dois grupos desiguais e comprimento de
segmento em 16 bits). A faixa 1–16 é dimensionada pelo pior caso do BR Code:
somando o teto de cada campo que `internal/pixbrcode` emite, o payload máximo
tem 243 bytes, e a versão 14 no nível M já carrega 362.

## Escala medida

`tools/generate-pix-qrcode-benchmark-evidence` roda os benchmarks reais nas duas
escalas que este repositório cobra de dependência nova (10.000 e 100.000
iterações, fixadas por `-benchtime=<N>x`, e não pelo dimensionamento automático
do Go) e grava a linha em `data/ops/pix_qrcode_benchmark_evidence.jsonl`, com a
carga do host junto — `ns/op` medido com o load em 10 não é o mesmo número que
com o load em 1, e sem isso uma regressão aparente seria indistinguível de um
vizinho barulhento.

O caminho medido é o completo — montar o payload, codificar o símbolo e a volta
obrigatória —, e não a biblioteca isolada: é o custo por cobrança que decide se
o Pix aguenta escala. Os três benchmarks separam onde o tempo mora: codificação
(biblioteca), desenho do PNG (nosso, cacheável por payload, já que o mesmo BR
Code sempre produz o mesmo símbolo) e leitura de volta (nossa).

## Validação

```
./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./internal/pixqrcode/
./tools/run-heavy-throttled ./tools/go-modern test -count=1 ./internal/codex2policyenforcement/
./tools/go-modern run ./cmd/check codex2-policy-enforcement
./tools/check-sca-govulncheck-evidence
./tools/generate-pix-qrcode-benchmark-evidence
```
