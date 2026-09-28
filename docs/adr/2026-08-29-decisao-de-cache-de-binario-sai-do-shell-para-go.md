# ADR: a decisão de cache de binário Go sai do shell para um pacote Go testável

Date: 2026-08-29

## Decision

A lógica que decide **"o binário em cache ainda serve?"** passa a viver em
`internal/gobincache`, um pacote Go com testes de comportamento, em vez de
Python embutido em heredoc dentro de `tools/run-go-cmd-cached`.

A migração é por **estrangulamento**, não por substituição: o pacote nasce
completo e testado, um wrapper de baixo risco passa a usá-lo primeiro, e o flip
dos demais acontece por medição. `run-go-cmd-cached` continua no caminho de
todo comando Go do repositório e não é reescrito de uma vez.

O cache de binário **permanece** — ele é justificado por medição, não por
hábito. O que muda é onde a decisão mora.

## Context

`tools/run-go-cmd-cached` tem **3.909 linhas de shell**, das quais **1.711 são
Python embutido em 13 heredocs** (44% do arquivo), com 81 funções.

O auditor desse wrapper, `internal/contract/checkmeta`, verifica-o com **185
asserções `strings.Contains` sobre o TEXTO do script**, contra **31** que o
executam de fato. Isso não é detalhe de estilo: é a causa de três defeitos
medidos.

1. **Asserções envelhecem em massa e ninguém vê.** Dezesseis testes
   determinísticos ficaram vermelhos porque o wrapper passou por um redesenho
   (grace period, fila supervisionada, artifact-claim endurecido) e o shard de
   teste não acompanhou. Um teste de substring quebra em refatoração inócua e
   passa quando o comportamento quebra sem mudar o texto.

2. **Duas asserções chegaram a se CONTRADIZER, por meses.**
   `TestCachedGoRunnersProvideExecutionTimeout` proíbe `--kill-after`;
   `TestRunGoCmdCachedCapsBuildBudgetUnderHeavyTimeout` exige o mesmo
   `--kill-after`, que o wrapper usa em 17 pontos. Cronologia: a proibição é de
   `8508cd73` (2026-06-28), o uso é de `dad121a3` (2026-07-21). As duas
   mensagens de commit são só o título — nenhuma razão registrada de nenhum
   lado. Dois testes de texto podem se contradizer sem que nada quebre, porque
   nenhum dos dois executa coisa alguma.

3. **Um laço de auditoria mostrava 1 violação onde havia 189**, porque parava no
   primeiro `t.Fatalf` — e o primeiro era, por acaso do alfabeto, falso
   positivo.

## Evidence

Medições desta máquina, 2026-08-29, com cache do Go quente:

| operação | tempo |
|---|---|
| `go build -o <path> ./cmd/check`, **nada** mudado | **5,19 s** |
| `go build -o <path> ./cmd/check`, build real com link | 19,28 s |
| `go list -f '{{.Stale}}'` sobre `./cmd/check` | 5,65 s |
| **hot path do wrapper**, cache válido (3 invocações) | **2,73 / 2,64 / 2,60 s** |
| `go build -o` de um `cmd/` mínimo do repo, nada mudado | **0,01 s** |
| `go build -o` de um main trivial fora do módulo, 2ª vez | 0,09 s |

Leitura, item a item:

- **O cache de binário é legítimo.** O Go pula o link quando nada mudou, mas
  ainda gasta ~5 s reconferindo o grafo de 488 pacotes. Com 330 gates, isso é
  ~27 min por passada. O wrapper corta para 2,6 s.
- **O ganho é menor do que se supunha.** 5,19 → 2,64 s é economia de ~2,5 s por
  invocação, não de 5. Um wrapper de 3.909 linhas para economizar 2,5 s é o
  desequilíbrio que motivou este ADR.
- **A recursão fecha.** Um `cmd/` que exponha o decisor se mantém atualizado em
  **0,01 s** — o decisor não precisa de cache para decidir sobre o cache.

Raio de alcance, medido:

```
grep -rl 'run-go-cmd-cached' tools/ .githooks/ | wc -l   ->  179
grep -rl 'run-heavy-throttled' tools/ .githooks/ | wc -l ->  125
```

## O que NÃO muda

O racional técnico do desenho anterior está **preservado**, com os comentários
migrados:

- **Identidade por build ID, não por sha256 do conteúdo.** Um sha256 de binário
  de ~240 MB custa 1,2–1,5 s de CPU e a checagem roda várias vezes por
  invocação. O Go embute um build ID derivado do conteúdo numa nota ELF perto do
  início do arquivo: ler é O(1) no tamanho e falha fechado em truncamento,
  corrupção, artefato velho ou rebuild.
- **Isso NÃO é a heurística de mtime**, que o desenho anterior rejeitou
  explicitamente e com razão: aquela confia em "mais novo", e cache restaurado
  forja timestamp. Aqui mtime, inode e tamanho entram **combinados** a uma
  igualdade de build ID — identidade autenticada, não ordenação.
- **`O_NONBLOCK | O_NOFOLLOW`.** Um FIFO no lugar do binário faz a leitura
  BLOQUEAR até alguém escrever do outro lado, e gate que trava é pior que gate
  que reprova. Symlink permitiria apontar o cache para binário alheio.

A stdlib do Go já expõe o que o Python inline reimplementava: `debug/buildinfo`
lê a nota, `syscall.Stat_t` dá dev/ino/mtime.

## Scope

Permitido nesta etapa:

- `internal/gobincache` — Observe, Matches, Decide, com motivo legível sempre;
- testes de comportamento no mesmo pacote;
- migração de **um** wrapper de baixo risco, medido lado a lado.

Fora desta etapa, e por decisão explícita:

- reescrever `tools/run-go-cmd-cached`;
- tocar `tools/run-heavy-throttled` ou `tools/run-generate-supervised`;
- remover qualquer asserção do `checkmeta` antes de a capacidade equivalente
  estar coberta por teste de comportamento.

Cada capacidade migrada mata a asserção de texto correspondente. É assim que os
185 greps viram testes de verdade — progressivamente, com o verde do
`checkmeta` como baseline de onde o estrangulamento parte.

## Consequences

**Ganho principal, e ele não é velocidade:** a decisão vira testável. Os oito
testes do pacote constroem um binário Go real e submetem ao caso adverso —
binário truncado, FIFO que travaria a leitura, symlink, flags de build
diferentes, troca de arquivo com mesmo conteúdo e inode novo. Nenhum deles é
`strings.Contains`.

**Risco assumido:** duas implementações da mesma decisão convivem durante o
estrangulamento. É deliberado — 179 wrappers dependem do caminho atual, e o
contrato de zero-regressão deste repositório proíbe trocar de uma vez o que
funciona em produção. A convivência termina quando a última capacidade migrar,
não antes.

**Dependência nova:** nenhuma. `debug/buildinfo` e `syscall` são stdlib.
Nenhum cadastro, credencial ou serviço externo.

## Verification

```
./tools/go-modern test -count=1 ./internal/gobincache/   -> ok, 8/8
```

Os oito, e o que cada um prova:

| teste | prova |
|---|---|
| `ReaproveitaOMesmoBinario` | o caminho feliz não regrediu |
| `RecusaBinarioTruncado` | cache interrompido no meio da cópia é pego pelo build ID |
| `RecusaSemTravarEmFIFO` | a guarda `O_NONBLOCK` existe — o teste tem prazo próprio e falha por estouro se ela sumir |
| `RecusaSymlink` | `O_NOFOLLOW` — link permitiria apontar o cache para binário alheio |
| `RecusaBinarioAusente` | falha fechada |
| `RecusaFlagsDeBuildDiferentes` | `-tags`/`-gcflags` fazem parte da identidade |
| `RecusaTrocaDeArquivoComMesmoBuildID` | o inode está na identidade: outra frente instalando entre a decisão e o exec é vista |
| `MotivoNomeiaSempreACausa` | nenhuma reprovação sai sem dizer por quê |
