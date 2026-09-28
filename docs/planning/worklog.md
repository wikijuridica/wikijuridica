# Worklog

O ledger canônico deste repositório é **`docs/goal/MAESTRO_CODEX_LOG.md`**, pela
seção 11 do `CLAUDE.md`. É lá que mora o relato completo de cada frente, com a
medição que o sustenta.

Este arquivo existe porque o plugin `stem` roda hooks `Stop` e `PreCompact` que
procuram `docs/planning/worklog.md` por caminho fixo e barram o fim do turno
quando não o encontram. Ele registra, em resumo, o que foi mudado e por quê, e
aponta para a entrada correspondente no ledger. Duas fontes divergirem seria pior
que uma só, então aqui fica o resumo e lá fica o argumento.

---

## 2026-09-08 — o custo dos hooks do Claude Code, medido e cortado

Entrada completa em `docs/goal/MAESTRO_CODEX_LOG.md`. Commits: `bd2b5064`,
`fbacb4a9`, `14aa9411`. Plano com a tabela dos 48 plugins em
`~/.claude/plans/voc-o-engenheiro-concurrent-neumann.md`.

O dono pediu um plano de configuração, plugins, skills e MCPs do Claude Code, com
uma condição: medir antes de desligar, e preferir manter e otimizar. A medição
mudou o diagnóstico intuitivo.

| medida | antes | depois |
|---|---|---|
| `Bash` com o comando `true` | 14,83 s | **0,88 s** |
| plugins efetivos no wiki | 44 | 24 |
| contexto do primeiro request | 130.448 tok | a medir em sessão nova |

Os 94% de queda vieram de quatro variáveis no `env` do `.claude/settings.json`,
sem desligar plugin: `RUFLO_HOOK_SKIP_NPX=1` (o plugin rodava
`npx ... ruflo@latest` no `Pre` e no `Post` de todo `Bash`, com timeout de 30 s),
`ECC_HOOK_PROFILE=minimal`, `ECC_SESSION_START_MAX_CHARS=4000` e
`ECC_GATEGUARD=off`. As variáveis entraram em vigor sem reiniciar a sessão.

Vinte plugins saíram **no escopo do wiki**, com o global intocado nos 48. Três
motivos: conflito com o contrato deste repositório (`ringmaster` barrava a
gravação de histórico, `taskplane` saía com `exit 2` em `Write`/`Edit`/`Task`,
`security-guidance` chamava a API Anthropic no `Stop` fora da conta do dono),
domínio errado (`carta-*`, os cinco `pilot-*`, `agentic-ml`) e redundância ou
morte (`superpowers-optimized` duplica 13 skills e escreve no repositório,
`crewai-skills` está vazio, `mempalace` e `openviking-memory` têm MCP que não
sobe). `academic-research-skills` saiu por licença: CC-BY-NC num portal que capta
cliente.

O `ringmaster` foi o caso que exigiu engenharia em vez de decisão. Ele nega toda
gravação de histórico por hook e não expõe knob nenhum — zero `RINGMASTER_*`,
zero `getenv`, e o cabeçalho do `guardrails.py` declara o desenho. Com o dono
mandando consertar, `ops/claude-code/patch-ringmaster-vcs-knob` acrescenta o knob
que faltava, liberando uma lista fechada de sete verbos e mantendo produção,
publicação, corte de release e PR barrados.
`ops/claude-code/test_patch_ringmaster_vcs_knob.py` prova isso por mutação em 15
casos, e foi ele que pegou os dois erros das versões anteriores do patch: a
primeira liberava a publicação de pacote junto, a segunda ainda deixava passar o
corte de release pela CLI da forja.

`tools/check-claude-code-hooks-latency` nasceu nesta sessão para medir as três
coisas de uma vez: inventário de hooks, custo observado no transcript e bench por
hook. A refutação adversarial achou um defeito nela — lia só o `enabledPlugins`
global e inflava 44 para 48 —, corrigido em `14aa9411`.

`.mcp.json` registra o MCP que o portal já serve em `POST /mcp`: 10 ferramentas,
HTTP 200 em 8,9 ms. Até então o Claude Code carregava Adobe com 86 ferramentas e
não carregava o servidor do próprio projeto.

Dois falsos positivos ficaram documentados na camada certa. O `grounding-guard`
acusa toda pseudo-versão do `go.mod` de fabricada, porque o proxy do Go só lista
tags; `.gguard.json` registra a exceção com o motivo, sem tocar no `go.mod`, cuja
integridade o `go.sum` já garante. E o `git gc` — que a primeira versão do plano
mandava rodar como passo de menor risco — apaga por padrão: são 9.541 objetos
inalcançáveis hoje, e o comando correto seria `git gc --no-prune`. Ele saiu do
caminho automático.

---

## 2026-09-08 — erros de hook do SessionStart

Nove linhas de erro no boot da sessão, quatro causas distintas, nenhuma delas no
harness. Entrada completa em `docs/goal/MAESTRO_CODEX_LOG.md`, seção
"2026-09-08 — as quatro causas dos erros de hook do SessionStart, medidas".

| erro | causa medida | o que foi feito |
|---|---|---|
| `Permission denied` (6×) | `dispatch.sh` de `carta-crm/1.11.0` e `carta-cap-table/6.68.3` instalado `644`, invocado direto pelo `hooks.json` | `chmod +x` nos dois |
| `hookSpecificOutput` sem `hookEventName` | `stem` emitia o objeto sem o campo que o schema exige | campo acrescentado no cache e no clone |
| `bd: not found` | `beads` declara `bd prime` e não embarca binário | `@beads/bd@1.2.2` instalado, fixado na versão do plugin |
| `headroom: not found` | CLI existe só no PyPI (`headroom-ai`) | plugin desativado |

O instalador de plugins preserva o bit de execução — `run-hook.cmd` do
`stackhawk-hawkscan`, do mesmo marketplace, chegou `755` —, então o defeito dos
dois plugins da Carta é de empacotamento, a montante.

O `headroom` não foi instalado de propósito: `headroom init hook ensure`
(`headroom/cli/init.py:845`) reescreve o `~/.claude/settings.json` do dono e sobe
um proxy local no caminho de toda requisição, com `PreToolUse` de 15 s em cada
chamada de Bash. Adotar isso é decisão do dono, não conserto de erro.

Verificação: os nove hooks reexecutados com carga de `SessionStart` real devolvem
`exit=0` e JSON válido; `bd prime` a partir da raiz devolve `exit=0` e não cria
`.beads/`. Confirmação final na próxima abertura de sessão.

Duram `bd` e a desativação do `headroom`. O `chmod` e o patch do `stem` vivem em
`~/.claude/plugins/cache/` e morrem no próximo `/plugin update`.

---

## 2026-09-08 — bootstrap do DeerFlow para desenvolvimento local

Pedido do dono: clonar o `bytedance/deer-flow` se preciso e prepará-lo para
desenvolvimento local seguindo o `Install.md` do próprio repositório. O clone já
existia em `/opt/wiki/deer-flow`, em `48bbea6d`, com `origin` apontando para
`https://github.com/bytedance/deer-flow.git`.

| passo | resultado |
|---|---|
| `make config` | criou `config.yaml`, `.env` e `frontend/.env` a partir dos templates |
| `make docker-init` | `exit=0`; sandbox em modo `local`, nenhuma imagem baixada |
| `docker compose config -q` | `exit=0` depois da correção do Compose |

O `make docker-start` do dono reprovou em `Docker Compose 1.29.2 is too old — 2.24.0
or newer is required`. A causa é o `docker-compose-dev.yaml`, que marca `env_file`
opcional na forma longa `- path: … / required: false`, sintaxe que o cliente v1 do
Debian não analisa. Instalado o plugin v2 oficial em
`~/.docker/cli-plugins/docker-compose`, versão `v5.5.1`, Apache-2.0, binário de
release do GitHub. É instalação de usuário, sem `sudo` e sem pacote de sistema, o
que respeita a regra do `Install.md` contra instalação privilegiada sem
autorização. O `_probe_compose` do `scripts/docker.sh` prefere o plugin v2, então
o `docker-compose` 1.29.2 do sistema continua no disco, intocado, e nada mais o
seleciona.

O clone é repositório git próprio aninhado dentro do `/opt/wiki` e estava
untracked. Acrescentada a linha `/deer-flow/` ao `.gitignore` do wiki: classifica o
ruído sem apagar nada e fecha a porta ao `git add` por diretório, que já varreu
trabalho de outra sessão três vezes neste projeto.

Pendência do dono, e só dele: o bloco `models` do `config.yaml` está inteiramente
comentado. Sem ao menos uma entrada e a chave correspondente, o DeerFlow sobe e não
responde. O arquivo referencia dezenas de nomes de variável do tipo
`$OPENAI_API_KEY` e `$VOLCENGINE_API_KEY`; nenhum arquivo de segredo foi aberto
para conferir valores, conforme o `Install.md` manda.

Nenhum serviço foi iniciado. O primeiro comando de lançamento continua sendo
`make docker-start` a partir de `/opt/wiki/deer-flow`.

## 2026-09-08 — reporter do TDD Guard ligado à suíte Go

O plugin `tdd-guard` foi instalado na sessão e a skill de setup pede um reporter
por framework de teste. Levantados os três candidatos do repositório: 1.564
arquivos `_test.go`, 148 testes Python e um `package.json` sem suíte. Só o Go
recebeu reporter. Os testes Python são todos `unittest` (127 de 127 arquivos
importam `unittest`, zero importam `pytest`, e o `pytest` não está instalado), e o
TDD Guard não publica reporter de `unittest`; instalar `pytest` para contornar isso
seria instalar um framework de teste novo, que a própria skill proíbe. O
`package.json` declara `"test": "echo \"Error: no test specified\" && exit 1"` e
nenhuma dependência de teste, então não há o que reportar ali.

Instalado `tdd-guard-go` v0.2.1 (MIT) por `go install`, em `~/go/bin`, que já está
no PATH. A versão é fixada de propósito: `@latest` num binário que decide o estado
da suíte muda o veredito sem mudar o repositório. O módulo não entra no `go.mod` e
não toca o grafo de atestação.

A receita genérica do TDD Guard é `go test -json ./... | tdd-guard-go`, e ela não
roda aqui: o padrão full-tree é barrado pelo `.claude/hooks/block-heavy-go.sh` com
exit 2 e por `permissions.deny`. O alvo de teste nasceu como
`tools/run-tdd-guard-test`, que exige pacote explícito, chama o Go pelo
`./tools/go-modern` e documenta no cabeçalho a forma envelopada para a suíte
inteira (`./tools/run-heavy-throttled ./tools/run-tdd-guard-test ./internal/...
./cmd/...`).

O ponto delicado do wrapper é o código de saída, porque ele é um cano. Sem
`pipefail`, `$?` devolve o código do reporter, que sai zero mesmo com a suíte
vermelha. Com `pipefail`, o cano devolve o último código não-zero, então um
reporter quebrado pinta de vermelho uma suíte verde. As duas formas erram, e o
wrapper lê `PIPESTATUS`: o código do `go test` manda, e a falha do reporter sai com
mensagem própria, porque é o único aviso de que o TDD Guard ficou cego. Um detalhe
custou uma rodada vermelha e virou comentário no arquivo: `PIPESTATUS` é volátil, a
primeira atribuição já zera o array, e ler `PIPESTATUS[1]` na linha seguinte aborta
com `unbound variable`. O array inteiro se copia num comando só.

`tools/test_run_tdd_guard_test.sh` trava os cinco casos e entra sozinho na suíte
diária pela descoberta do passo 2c-bis do `run-qualidade-diaria`. O teste foi
escrito antes do wrapper e reprovou pelo motivo certo. Provado por mutação depois:
a forma ingênua (sem `pipefail`, com `$?`) reprova no caso 3, e a forma com
`pipefail` e `$?` reprova no caso 5, enquanto o arquivo real passa. O pacote-alvo é
`./internal/pageinline/`, o menor do repositório com teste, para que a suíte diária
pague segundos por isso.

Os arquivos que o guard escreve em `.claude/tdd-guard/data/` são estado de rodada e
foram classificados no `.gitignore`, com exceção do `instructions.md`, que é
configuração e fica versionado.

## 2026-09-08 — pipx na máquina e Scrapy fora do Python do sistema

O pedido chegou como `apt install python3-xyz` reprovando. O pacote não existe e
nunca existiu: `xyz` é o marcador literal que o Debian imprime na mensagem do PEP
668, `error: externally-managed-environment`, quando o `pip` recusa escrever no
Python do sistema. O interpretador aqui é o 3.11.2 e o
`/usr/lib/python3.11/EXTERNALLY-MANAGED` está no lugar, então a recusa é o
comportamento correto e não havia defeito a corrigir na origem do erro.

A lacuna real era de ferramenta. A máquina tinha o `venv` da biblioteca padrão e
mais nada: sem `pipx`, sem `virtualenv`, sem `python3-full`. Instalei `pipx`
1.1.0-1 e `python3-full` 3.11.2-1+b1 do `bookworm/main`, ambos do repositório
oficial, e o `pipx ensurepath` confirmou que `~/.local/bin` já constava do
`.profile` e do `.bashrc`.

O alvo era o Scrapy. O `apt` oferece `python3-scrapy` 2.8.0-2, dez versões menores
atrás do que está publicado, e instalá-lo prenderia o framework ao Python do
sistema junto de toda a árvore de dependências. Ficou pelo `pipx`, que deu o
`scrapy` 2.18.0 num venv próprio em `~/.local/pipx/venvs/scrapy` com o executável
exposto por symlink. `scrapy version -v` responde com Twisted 26.4.0, lxml 6.1.3 e
libxml2 2.14.6, exit 0. Para `import scrapy` dentro de um script, o interpretador é
o `~/.local/pipx/venvs/scrapy/bin/python`, ou um venv de projeto próprio — o
symlink cobre só a linha de comando.

Um ruído apareceu de lado e não é defeito deste repositório: toda operação de
`apt` imprime `Impossível ler /etc/apt/sources.list.d/cloudflare-client.list`,
porque o arquivo está em modo 600 com dono `root`. O aviso não altera resolução de
pacote nem código de saída.

## 2026-09-08 — pip padrao no user-site, e Scrapy e crawl4ai fora de venv

A entrada anterior parou no `pipx`, que resolve a linha de comando e nada mais.
O pedido seguinte mostrou que a rota estava errada para o caso do dono: ele quer
`import` funcionando em qualquer diretorio, sem venv por projeto e sem reinstalar
o mesmo pacote em cada caminho. O `pipx` faz o oposto disso — um venv por
aplicativo, invisivel para o interpretador do sistema.

A leitura do estado real deu a resposta. `~/.local/lib/python3.11/site-packages`
ja tinha 120 pacotes, `torch 2.12.1+cpu` entre eles, e `site.ENABLE_USER_SITE` era
`True`. O padrao de facto desta maquina sempre foi o user-site; o que faltava era
declara-lo. `~/.config/pip/pip.conf` nasceu com `user = true` e
`break-system-packages = true`, e a combinacao e segura: o `pip` passa a escrever
so no user-site, que tem precedencia no `sys.path`, enquanto o Python de
`/usr/lib/python3/dist-packages` instalado por `apt` fica intacto. Nao havia
config anterior — `~/.pip/pip.conf`, `/etc/pip.conf` e o proprio arquivo nao
existiam, e `pip config list` voltava vazio.

Com isso, `pip install -U scrapy crawl4ai` pousou `scrapy` 2.18.0 e `crawl4ai`
0.9.3 no user-site, com Playwright 1.62.0 e Twisted 26.4.0 na esteira, e o
`import` responde igual de `/tmp` e de `/opt/wiki`.

A instalacao deixou uma regressao propria que precisou de correcao na origem. O
`chardet` subiu para 7.6.0 no user-site enquanto o `requests` continuava sendo o
2.28.1 do `apt`, e todo `import requests` na maquina passou a imprimir
`RequestsDependencyWarning` em stderr. Suprimir o aviso seria mascarar; a causa
era a versao velha do `requests`, entao ele e o `urllib3` subiram para 2.34.2 e
2.7.0 no user-site e o aviso saiu. Nenhum dos 289 arquivos Python rastreados deste
repositorio importa `requests` ou `urllib3`, entao a troca para o `urllib3` 2.x
nao alcanca codigo daqui.

Dois residuos ficaram registrados. O `ocrmypdf` 14.0.1+dfsg1 reclama de
`deprecation 2.0.7` contra o `>=2.1.0` que pede, conflito anterior a esta sessao e
que nao impede o binario de responder. E `/etc/apt/sources.list.d/cloudflare-client.list`
estava em modo 600, fazendo toda operacao de `apt` imprimir
`Impossivel ler`; o arquivo carrega apenas a linha `deb [signed-by=...]` do
repositorio publico do Cloudflare, sem credencial, entao foi para 644, que e o
modo dos demais `.list`, e o `apt` voltou a rodar com zero avisos.

## 2026-09-08 — folga de disco: 258 GB liberados na particao raiz

O gate de espaco deste repositorio, `tools/check-disk-headroom`, estava
reprovando: `/` tinha 29,72 GiB livres contra um piso de 136,28 GiB. Durante a
apuracao a situacao piorou — um `pip install vllm` disparado de outra sessao
levou a particao a 4,9 GiB e o gate teria ficado sem margem alguma.

A premissa de partida estava errada em dois pontos, e os dois importam para quem
for medir disco aqui de novo. Primeiro: o SSD nao estava cheio, a particao `/`
estava. `/storage` (`/dev/nvme0n1p1`) e a segunda particao do **mesmo** NVMe
KINGSTON e tinha 264 GiB ociosos, com a mesma velocidade. Segundo: `/opt/divorcio`
nao era o vilao — sao 7,6 GiB, e e um bind mount de `/opt/pool-divorcio`, o que
faz um `du` ingenuo contar a arvore duas vezes.

Nada deste repositorio foi alterado. O que mudou foi o entorno, e dois itens
alcancam o build Go daqui: `~/.cache/go-build` (72 GiB) e `/root/.cache/go-build`
(22 GiB) agora vivem em `/storage`, atras de symlink. A escolha de `/storage` em
vez do HDD foi deliberada: `/mnt/hdd` e um WDC WD10SPZX de 5400 rpm, e cache de
compilacao em disco rotacional degradaria o build. Verificado antes de mover —
`go build` com `GOCACHE` atras de symlink retorna 0 e grava no alvo real. Os
caches de modulo (`~/go/pkg/mod`, `/root/go/pkg`) seguiram o mesmo caminho.

Para o HDD foram apenas dados frios: tarballs de backup, imagem do GNOME Boxes,
sessoes e log do Codex, SDK Android, ISOs do Windows e a arvore arquivada do
divorcio. Cada item so teve a origem removida depois de `rsync -n
--itemize-changes` vir vazio e a contagem de arquivos bater dos dois lados.

`/` fechou em 324 GiB usados, 288 GiB livres, 53%. O gate voltou a aprovar:
`check-disk-headroom: ok — piso congelado ate 2026-09-09T00:00Z`.

Fica registrado um achado que e decisao do dono, nao minha: `/opt/wiki` guarda
298 diretorios de topo nao rastreados e nao ignorados, 290 deles com `.git`
proprio — `kubernetes`, `tensorflow`, `microsoft/TypeScript`, `ToolJet`, `refine`,
`roslyn`, `next.js`, `grafana`, `elasticsearch`, `spark`, `cpython`, `php-src`,
`rails` e outros, criados entre 07/09 17:22 e 08/09 09:28, somando ~106 GiB. O
repositorio em si tem 4,36 GiB por `git count-objects`. Nao toquei em nenhum
deles. Se forem corpus descartavel, e o maior ganho de espaco disponivel nesta
maquina.

Ledger completo da migracao, com verificacao e rollback por item:
`/mnt/hdd/arquivo/LEDGER-migracao-2026-09-08.md`.
