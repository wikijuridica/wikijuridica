---
paths:
  - "data/ai/fila.sqlite"
  - "internal/cerebro/**"
  - "cmd/cerebro/**"
---

# Fila do cerebro — a identidade inclui o modelo, e trocar de modelo custa load

Memoria de origem: `ollama-troca-de-modelo-custa-load.md` (a secao do custo de
load). A fisica do host e o tuning vivo ficam em `ollama-e-earlyoom.md`. Casos
medidos, tabelas de tempo e paragrafos SUPERADOS: `docs/ops/FILA_DO_CEREBRO_CASOS.md`
(movidos literais em 2026-09-23). Aqui: veredito, ordem e comando.

`internal/cerebro/fila.go`. A identidade da tarefa inclui o **modelo**; mesmo
`texto_sha256` nunca e' recomputado. `estado` e' `pendente|executando|concluida|erro`;
colunas novas entram por `ALTER TABLE ADD COLUMN` e **nunca estado novo** (o
`CHECK(estado IN ...)` obrigaria recriar a tabela): `superada_em` e' a LAPIDE (erro
cujo trabalho uma irma ja concluiu); `recuperacoes` conta mortes do worker,
restituidas ate `TetoDeRecuperacoesSemCulpa` = 6; `falhou_com` e' o SHA-256 de
`/proc/self/exe` (`CarimboDoBinario`) — nem `os.Executable()` (o deploy troca por
`mv`) nem `debug.ReadBuildInfo()` (`+dirty`).

## A cura decide por CAUSA, e termina

`curavel <=> estado='erro' E superada_em='' E falhou_com <> carimbo atual`: so'
codigo novo muda o resultado (a entrada esta congelada em `impressao`).
`tentativas=0` nao e' freio. Quem cura e' `ReabrirCuraveis` no BOOT de `cerebro
servir` (depois de `Recuperar` e `MarcaLapidesDeIrmaConcluida`); `cerebro reabrir
--curaveis` chama a mesma funcao. `Reabrir` exige `superada_em=''` e reaplica a
FAIXA VIGENTE (dentro fica; fora vai para a base; tipo sem faixa fica);
`SanaLapidesAmbulantes` desfaz `pendente` com lapide no boot.
Obsolescencia e' `ErrTrabalhoSuperado` -> `Fila.Superar`, checada antes de
`naturezaDaFalha`. "Nao e' nova" nao e' "esta na fila": `concluida` sem resultado no
indice volta por `ReabreConcluidaSemResultado`. Controle de falso positivo:
`cura_por_causa_test.go`.

## Orfa, lease e o que NUNCA se auto-cura

Escrituracao (`Falhar`, `Concluir`, `Devolver`, `Superar`) por `Worker.escritura`:
insiste so' em `bancoOcupado` (5, 6, 261, 262, 517) ate `TetoDeEsperaPorBanco`
(180 s) — espera sem teto e' mascaramento. `RecuperarVencidas` roda no laco (5 min)
com lease `prazoDoLote(maxLote) + MargemDaEscrituracao + MargemDoBatimento`; lease
`<= 0` e' recusado; `Recuperar` so' no boot.
Para e alerta, sem cura: fila corrompida (`quick_check`), erro de SQLite fora de
`bancoOcupado`, carimbo indeterminado, `recuperacoes >= 6`, pausa manual vencida
(nunca se auto-limpa), contencao alem do teto; lapide e `concluida` com resultado nao
sao defeito. Gate: `lapide_ambulante` por PRESENCA, `executando_vencida` por DURACAO,
`cura_nao_rodou` por FLUXO (`curaveis_paradas > 0`), nunca pelo estoque de `erro`; o
gate le `carimbo_binario` do batimento, nao o recalcula.

## `Devolver` x `Falhar`

INFRA (`ErrIndisponivel`, `ErrServidor`, `ErrModeloAusente`, prazo, cancelamento) =>
`Fila.Devolver`, sem gastar tentativa, jitter ±20%. CONTEUDO (`ErrRecusado`,
`ErrRespostaIlegivel`) => `Fila.Falhar`. O disjuntor e' do WORKER (30 s -> 15 min) e
so' fecha depois do laco por tarefa, com `devolvidas == 0`.

## Caminho quente

Toda consulta no caminho de cada Passo tem **um** caminho inequivoco (rowid, indice
com prefixo de igualdades + `ORDER BY`, ou `+coluna`), estados vivos NOMEADOS (nunca
`<>'erro'`) e teste de `EXPLAIN QUERY PLAN` sobre a **constante** da producao. **Nunca
ANALYZE como correcao.** Contagem por `GROUP BY estado`, nunca `SUM(condicao)`;
`idx_tarefa_estado_modelo` = (estado, modelo); `idx_tarefa_elegivel` = (estado,
prioridade DESC, id, disponivel_em), redefinido no `Abrir`; `sqlReivindicaLote` usa
`+tipo`/`+modelo` (pior caso O(P) na troca de faixa: nomeado, nao fechado). `Passo`
espera `TetoDaReivindicacaoOcupada` (60 s) antes de pausar `infra/fila_ocupada`;
`EnfileirarLote` repete em BUSY e funde as marcas so' depois do commit; o batimento
carimba `ultimo_lote_em` so' depois de `Concluir`.

## Faixas e troca de modelo

Faixas de 100 pontos em `internal/cerebro/tarefas.go` (`FaixasDeclaradas`),
`min(faixa_n) > max(faixa_{n+1})`: `FaixaEmbeddings` 0, `FaixaComentarios` −100,
`FaixaExtracao` −200, `FaixaMedicao` −300. Faixa nova so' ali, nunca num `flag.Int`;
estoque legado: `cerebro reprioritizar-faixas --aplicar` (ensaio e' o padrao). O lote
e' do mesmo `tipo`+`modelo` porque a troca custa mais que o prefill: sonda de geracao
nao roda durante a fila de embeddings, e custo de modelo se mede por `load_duration`.

## Politica vigente: nao travar por saturacao nem por CPU (ordem do dono, 2026-09-16/17)

`CargaMaxPadrao` = 0 e `LockPesadoPadrao` vazio (`internal/cerebro/saude.go`). Disputa
de CPU se resolve no peso de cgroup (`wikijuridica_alimentacao.slice`, `CPUWeight=20`)
ou rodando o pesado numa slice de peso maior — **nunca pausando a inteligencia**.

## Prazo por TIPO, lease pelo PIOR caso

`PrazoPorTarefaPadrao` = 300 s; `prazosPorTipo` so' com o que diverge
(`TipoRedigirNoticia: 900 s`). `leaseDeExecucao` usa `prazoMaximoDoLote`: lease menor
que o prazo de ALGUM tipo roda a tarefa duas vezes. `parede=45m0` com devolucao => o
alvo e' o PROMPT, nao o teto.

## O que nao mudar sem medir

- `OLLAMA_MAX_LOADED_MODELS` = 2; a guarda pesa bytes residentes (teto 9 GiB,
  `saude.go`).
- **Nao ha `DELETE` livre.** `Fila.Podar` so' `concluida` de tipo com artefato
  append-only (`PodavelPorTipo`). A linha em `erro` e' a unica evidencia do defeito.
- `MemoryMax=12G` em `ops/ollama/ollama.service.d/wikijuridica-tuning.conf`.
- Massa (embeddings, extracao, classificacao) em modelos de 0,6 a 4B; 14b so' noturno.
- Custo se corta em **tokens processados**, nunca em inteligencia: o prefill domina,
  entao prefixo de sistema reaproveitado, esquema curto e `num_ctx` por tarefa valem
  mais que trocar de modelo.
- Parser antes de modelo: meca a cobertura do parser sobre o ja rotulado.
