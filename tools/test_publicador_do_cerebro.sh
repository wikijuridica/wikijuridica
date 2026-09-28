#!/usr/bin/env bash
# Bancada do publicador autonomo do cerebro (§P6) — `tools/publicar-estoque` e
# as flags que a cadeia do §5 ganhou para poder ser APONTADA em vez de copiada.
#
# ★ O QUE ELA EXISTE PARA IMPEDIR, defeito por defeito
#
#   1. a cadeia apontada para o gatilho do publicador COMMITAR o shard da onda
#      (`alvos_do_registro` com o gatilho literal): o publicador de acordaos
#      commitaria sete shards alheios e NAO o proprio;
#   2. a passada do publicador RESOLVER o alerta da onda (chave literal
#      `onda-diaria` em `notify-owner`), fechando sozinho um alarme cuja
#      condicao ninguem curou;
#   3. a cadeia escrever historico por FORA de `tools/cerebro-commitar`. Em
#      systemd os hooks do CLI do Claude Code nao existem — sao da sessao, nao
#      do sistema —, entao a allowlist do wrapper e' a UNICA defesa la;
#   4. `--sem-coleta` continuar indo a rede, transformando cada peca redigida
#      pelo cerebro numa rodada de requisicoes a quatro fontes oficiais;
#   5. o publicador ler o manifesto pela chave errada — `intent_id` NAO existe
#      em `published_manifest.jsonl`, e procura-lo faz TODA pagina publicada
#      parecer pendente (a fila nunca esvaziaria);
#   6. a rotacao de shard (-02, -03) sumir da medicao de pendencia;
#   7. dado ilegivel virar "nada pendente" — ausencia de medicao lida como
#      ausencia de trabalho e' como uma fila para de drenar em silencio;
#   8. a vedacao de filesystem do `.git` VOLTAR as units: ela tornaria a ordem
#      do dono de 2026-09-16 inexequivel, porque commit legitimo escreve em
#      `.git` (a linha existiu e funcionou na manha do mesmo dia, sob a politica
#      anterior);
#   9. a reprovacao do pre-commit por CONTENCAO ser lida como defeito da peca —
#      medido: "compile closure excedeu 76.5s concedidos" reprovou um commit que
#      passou na retentativa sem uma linha alterada. Peca parada por defeito que
#      nao e' dela e' o "travar a toa" que o dono nomeou;
#  10. o contrario, e e' pior: tudo virar "ambiente" e um defeito real entrar em
#      laco infinito.
#
# ★ CENARIO PROPRIO, NUNCA O ESTADO DE PRODUCAO
#
# `tools/test_alvos_do_registro.sh` registra o precedente: um mutante passou a
# SOBREVIVER no dia em que o shard de acordaos nasceu, porque a fixture deixou
# de exercitar o cenario sem nada ficar vermelho. Aqui cada caso funcional roda
# sobre um repositorio de mentira montado em $TMPDIR, com `--raiz`.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
falhas=0

falha() {
	printf 'FALHA: %s\n' "$1" >&2
	falhas=$((falhas + 1))
}
# `-e` e' obrigatorio: sem ele um padrao que comeca com `--` vira OPCAO do grep
# e o teste passa a medir a mensagem de uso do proprio grep.
contem() { grep -qF -e "$2" <<<"$1" || falha "$3"; }
nao_contem() { grep -qF -e "$2" <<<"$1" && falha "$3"; }
# so_diretivas remove comentario: a unit DOCUMENTA que nao usa SuccessExitStatus
# nem ProtectHome=read-only, e uma assercao que le o comentario mede o texto em
# vez da regra -- exatamente o defeito de "comentario de teste que mente sobre
# cobertura".
so_diretivas() { grep -v '^[[:space:]]*#' <<<"$1"; }
confere() {
	if [[ "$1" != "$2" ]]; then
		printf 'FALHA: %s\n  esperado: %s\n  veio    : %s\n' "$3" "$2" "$1" >&2
		falhas=$((falhas + 1))
	fi
}

# ★ AUTO-CONFERENCIA DAS AJUDANTES, e ela nasceu de um falso-verde DESTA bancada
#
# Medido em 2026-09-16: sete assercoes chamavam `confere`, que nao existia neste
# arquivo (era da bancada irma). O bash imprimiu "comando nao encontrado" sete
# vezes, `falhas` continuou em zero e a bancada terminou dizendo **ok**. Teste
# que passa verde sem ter testado e' pior que teste ausente: o ausente nao
# mente.
for ajudante in falha contem nao_contem so_diretivas confere; do
	if ! declare -F "$ajudante" >/dev/null; then
		echo "FALHA: ajudante '$ajudante' nao definida — assercao que a use sairia como 'comando nao encontrado' SEM reprovar" >&2
		exit 1
	fi
done

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# ---------------------------------------------------------------------------
# 1. `alvos_do_registro` segue o GATILHO da passada, e nao um literal
# ---------------------------------------------------------------------------
# Extracao por ancora do arquivo REAL: copiar o corpo criaria uma segunda versao
# que envelhece sozinha.
corpo="$(sed -n '/^alvos_do_registro()/,/^}/p' "$RAIZ/tools/run-daily-content")"
[[ -n "$corpo" ]] || {
	echo "FALHA: nao achei alvos_do_registro em tools/run-daily-content" >&2
	exit 1
}

cenario="$tmp/cenario"
mkdir -p "$cenario/tools" "$cenario/data/editorial/v2_pages" "$cenario/data/editorial/portfolio_v2"
cat >"$cenario/tools/listar-produtores-de-pagina" <<'REGISTRO'
#!/usr/bin/env bash
# Registro de mentira com DOIS gatilhos, que e' o ponto do teste.
gatilho="$2"
if [ "$gatilho" = "publicador-cerebro" ]; then
	printf 'acordaos\t./cmd/gen-a\tdata/editorial/v2_pages/acordao-01.jsonl\tdata/editorial/portfolio_v2/acordao-01.jsonl\tE\t30\n'
else
	printf 'noticias\t./cmd/gen-n\tdata/editorial/v2_pages/noticia-01.jsonl\tdata/editorial/portfolio_v2/noticia-01.jsonl\tN\t40\n'
fi
REGISTRO
chmod +x "$cenario/tools/listar-produtores-de-pagina"
: >"$cenario/data/editorial/v2_pages/acordao-01.jsonl"
: >"$cenario/data/editorial/v2_pages/noticia-01.jsonl"

saida="$(cd "$cenario" && GATILHO=publicador-cerebro bash -c "$corpo"'; alvos_do_registro shard' 2>&1)"
contem "$saida" "acordao-01.jsonl" "com GATILHO=publicador-cerebro a funcao tem de devolver o shard do publicador"
nao_contem "$saida" "noticia-01.jsonl" \
	"o publicador commitaria o shard da ONDA: e' o defeito de gatilho literal que esta bancada existe para matar"

# O DEFAULT CONTINUA SENDO O DA ONDA — sem isso a bancada irma, que avalia esta
# mesma funcao sem GATILHO no ambiente, morreria sob `set -u`.
saida="$(cd "$cenario" && bash -c "$corpo"'; alvos_do_registro shard' 2>&1)"
contem "$saida" "noticia-01.jsonl" "sem GATILHO no ambiente o default tem de ser o gatilho da onda"

# ---------------------------------------------------------------------------
# 2. Os pontos de chamada da cadeia — a funcao pode estar certa e o chamador nao
# ---------------------------------------------------------------------------
fonte="$(cat "$RAIZ/tools/run-daily-content")"
contem "$fonte" '--rotulo "$ROTULO"' "check-onda-avanca tem de receber o rotulo da passada"
contem "$fonte" '--minimo "$MINIMO_NOVAS"' "o piso de rota nova tem de vir da flag, nao de um literal"
contem "$fonte" '--chave "$ROTULO"' "notify-owner tem de abrir alerta na chave da passada"
contem "$fonte" 'for chave in "$ROTULO" "unit-falhou-$UNIT_DA_PASSADA"' \
	"a resolucao de alerta tem de ser escopada na passada e na unit dela"
nao_contem "$fonte" '--rotulo "onda-diaria"' "rotulo literal voltou ao check-onda-avanca"
nao_contem "$fonte" '--chave "onda-diaria"' "chave literal voltou ao notify-owner"
# A unit das 12:20 invoca por este nome. Renomear a flag quebraria a unit viva.
contem "$fonte" '--somente-noticias) SOMENTE_NOTICIAS=1' "--somente-noticias tem de continuar aceito"

# ---------------------------------------------------------------------------
# 3. `--commit-restrito` so escreve historico pela PORTA UNICA
# ---------------------------------------------------------------------------
# A cadeia NUNCA invoca git de escrita no modo restrito: ela chama
# `commita_restrito`, que chama `tools/cerebro-commitar`. Em systemd os hooks do
# CLI do Claude Code NAO EXISTEM -- eles sao da sessao, nao do sistema --, entao
# a allowlist do wrapper e' a UNICA defesa la, e esta assercao e' o que impede a
# cadeia de contorna-la.
ramo="$(python3 - "$RAIZ/tools/run-daily-content" <<'PYRAMO'
import sys
# Recorta TODOS os blocos `if [ "$SEM_GIT" = "1" ]; then ... fi/else`, casando o
# fechamento pela MESMA indentacao da abertura. Ancora frouxa (`/^\tfi$/`)
# arrastaria o `else` junto e o teste passaria a ver o `git commit` do ramo
# normal -- falso vermelho que ensina a desligar o teste.
linhas = open(sys.argv[1], encoding="utf-8").read().split("\n")
saida, dentro, recuo = [], False, ""
for linha in linhas:
    despida = linha.lstrip("\t")
    if not dentro and despida.startswith('if [ "$COMMIT_RESTRITO" = "1" ]; then'):
        dentro, recuo = True, linha[: len(linha) - len(despida)]
        continue
    if dentro:
        # `elif` FECHA o bloco tanto quanto `fi` e `else`. Sem ele o recorte
        # atravessava a etapa 8.05/9 inteira e enxergava o commit do ramo
        # normal -- o teste reprovava codigo correto, que e' o jeito mais rapido
        # de ensinar alguem a desligar o teste.
        if linha == recuo + "fi" or linha == recuo + "else" or linha.startswith(recuo + "elif "):
            dentro = False
            continue
        saida.append(linha)
print("\n".join(saida))
PYRAMO
)"
contem "$ramo" 'commita_restrito portfolio' "o modo restrito tem de commitar o portfolio pela porta unica"
contem "$ramo" 'commita_restrito paginas' "o modo restrito tem de commitar o estoque pela porta unica"
contem "$ramo" 'commit_adiado_por_${CLASSE_DO_COMMIT}' "a reprovacao por ambiente/hook tem de virar RETOMADA, nao quarentena de conteudo"
# A assercao e' sobre EXECUCAO, nao sobre a string: a mensagem de quarentena
# NOMEIA, de proposito, os comandos que o Claude Code vai rodar depois, e um
# grep pela string reprovaria justamente o texto que existe para destravar.
# O que nao pode aparecer e' uma LINHA que invoque git de escrita -- direta ou
# pelo `com_teto`.
escrita_de_historico='^[[:space:]]*(git|com_teto [0-9]+ "[^"]*" git) (add|commit)\b'
if grep -qE "$escrita_de_historico" <<<"$ramo"; then
	falha "o modo restrito INVOCA git de escrita direto, contornando tools/cerebro-commitar -- em systemd o wrapper e' a UNICA defesa"
	grep -nE "$escrita_de_historico" <<<"$ramo" >&2
fi
# E nada em lugar nenhum pode APAGAR estoque: delecao de qualquer especie e'
# vedada nos dois lados do contrato.
nao_contem "$fonte" 'rm -rf data/editorial' "a cadeia nao apaga estoque"
nao_contem "$fonte" 'rm -f data/editorial' "a cadeia nao apaga estoque"

# ---------------------------------------------------------------------------
# 4. `--sem-coleta` zera o mapa de coletores
# ---------------------------------------------------------------------------
contem "$fonte" 'if [ "$SEM_COLETA" = "1" ]; then' "--sem-coleta tem de filtrar o mapa de coletores"
bloco_coleta="$(awk '/if \[ "\$SEM_COLETA" = "1" \]; then/,/^fi$/' "$RAIZ/tools/run-daily-content")"
contem "$bloco_coleta" 'unset "COLETORES[$chave]"' "--sem-coleta tem de REMOVER as fontes, nao so avisar"
# E o publicador tem de passar a flag: a funcao pode estar certa e o chamador nao.
#
# ★ CENARIO PROPRIO, e ele nasceu de a bancada ter ficado vermelha por producao.
#
# Ate 2026-09-16 esta assercao rodava `--seco` contra o repositorio REAL. No dia
# em que outra frente deixou 8 portfolios de acordao sem commit, o publicador
# passou a BLOQUEAR (corretamente) e a linha de comando nunca era impressa: a
# bancada reprovava um codigo correto porque a fixture era o estado de producao.
# E' o mesmo defeito que `fixture-que-muda-por-outro-motivo` registra.
cenario_cmd="$tmp/cmd"
mkdir -p "$cenario_cmd/ops" "$cenario_cmd/content" "$cenario_cmd/data/editorial/v2_pages" \
	"$cenario_cmd/data/editorial/portfolio_v2" "$cenario_cmd/data/ai" "$cenario_cmd/data/ops"
cat >"$cenario_cmd/ops/produtores-de-pagina.jsonl" <<'REGCMD'
{"canal":"noticias","cmd":"./cmd/gn","shard":"data/editorial/v2_pages/noticia-01.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-01.jsonl","gatilho":"onda-diaria","limite_env":"A","limite_padrao":40}
REGCMD
printf '{"schema_version":"cerebro_publicacao_v1","handle_do_autor":"x","modelo":"m","teto_por_execucao":5,"teto_de_tentativas_por_peca":2}\n' \
	>"$cenario_cmd/content/cerebro_publicacao.json"
printf '{"intent_id":"n-1"}\n' >"$cenario_cmd/data/editorial/v2_pages/noticia-01.jsonl"
printf '{"intent_id":"n-1"}\n' >"$cenario_cmd/data/editorial/portfolio_v2/noticia-01.jsonl"
: >"$cenario_cmd/data/editorial/published_manifest.jsonl"
printf '{"schema_version":"noticia_redigida_v1","link":"https://y/1","comentario":"PENDENTE","aprovada":true}\n' \
	>"$cenario_cmd/data/ai/noticias_redigidas.jsonl"
(
	cd "$cenario_cmd" || exit 1
	git init -q .
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base >/dev/null 2>&1
) || falha "nao consegui montar o cenario limpo"
seco="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$cenario_cmd" --seco 2>&1)"
nao_contem "$seco" "BLOQUEADO" "no cenario limpo nada pode bloquear: a assercao da linha de comando mediria outra coisa"
contem "$seco" "--sem-coleta" "publicar-estoque tem de chamar a cadeia sem coleta"
contem "$seco" "--commit-restrito" "publicar-estoque tem de chamar a cadeia pela porta de commit restrita"
nao_contem "$seco" "--no-verify" "nunca se pula o pre-commit: contorno vira a proxima peca quebrada"
contem "$seco" "--minimo-novas=0" "a passada de enriquecimento nao cobra rota nova; quem cobra e' a reconciliacao"

# ---------------------------------------------------------------------------
# 5. A chave do manifesto e' `unique_intent_id`
# ---------------------------------------------------------------------------
repo="$tmp/repo"
mkdir -p "$repo/ops" "$repo/content" "$repo/data/editorial/v2_pages" \
	"$repo/data/editorial/portfolio_v2" "$repo/data/ai" "$repo/data/ops"
cat >"$repo/ops/produtores-de-pagina.jsonl" <<'REG'
{"canal":"noticias","cmd":"./cmd/gen","shard":"data/editorial/v2_pages/noticia-01.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-01.jsonl","gatilho":"onda-diaria","limite_env":"WIKI_LIMITE_NOTICIAS","limite_padrao":40}
REG
printf '{"schema_version":"cerebro_publicacao_v1","handle_do_autor":"x","modelo":"m","teto_por_execucao":5,"teto_de_tentativas_por_peca":2}\n' \
	>"$repo/content/cerebro_publicacao.json"
printf '{"intent_id":"not-a-1","sections":[{"heading":"h","text":"corpo sem comentario"}]}\n' \
	>"$repo/data/editorial/v2_pages/noticia-01.jsonl"
# A pagina ESTA publicada, e so a chave certa enxerga isso.
printf '{"unique_intent_id":"not-a-1","path":"/noticias/a/"}\n' \
	>"$repo/data/editorial/published_manifest.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
contem "$saida" "pendentes acionaveis: 0" \
	"pagina no manifesto foi contada como pendente: a chave e' unique_intent_id, e intent_id NAO EXISTE ali"

# ---------------------------------------------------------------------------
# 6. Rotacao de shard: o -02 tem de entrar na medicao
# ---------------------------------------------------------------------------
printf '{"intent_id":"not-a-2","sections":[{"heading":"h","text":"corpo"}]}\n' \
	>"$repo/data/editorial/v2_pages/noticia-02.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
contem "$saida" "noticia-02.jsonl" "o irmao de rotacao tem de entrar na lista de shards"
contem "$saida" "pendentes acionaveis: 1" "a pagina do -02 nao esta no manifesto e tem de aparecer como pendente"

# ★ E A FAMILIA DE ROTACAO DO DRIVER USA A MESMA REGUA DA CADEIA E DA PORTA.
#
# `\d` do Python casa digito UNICODE; o glob `-[0-9][0-9].jsonl` de
# `alvos_do_registro` nao. Se o driver lesse `noticia-٠١.jsonl`, contaria como
# pendencia uma pagina que a cadeia nunca vai commitar — e a peca esgotaria o
# teto de tentativas sem defeito nenhum.
printf '{"intent_id":"not-a-9","sections":[{"heading":"h","text":"corpo que contaria"}]}\n' \
	>"$repo/data/editorial/v2_pages/noticia-٠١.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
nao_contem "$saida" "٠١" "o driver leu shard com ordinal UNICODE: a regua dele divergiu do glob da cadeia"
contem "$saida" "pendentes acionaveis: 1" "a contagem mudou com um arquivo que a cadeia nunca escreve"

# ---------------------------------------------------------------------------
# 7. Enriquecimento: comentario aprovado fora do estoque e' pendencia; dentro, nao
# ---------------------------------------------------------------------------
# ASPAS NO COMENTARIO SAO O PONTO DESTE CASO: prosa juridica cita tese e ementa
# entre aspas o tempo todo, e comparar contra o JSON SERIALIZADO faria cada `"`
# virar `\"` no estoque. A peca ficaria pendente PARA SEMPRE, esgotaria o teto
# de tentativas e seria PARADA sem nunca ter tido defeito nenhum.
printf '{"schema_version":"noticia_redigida_v1","link":"https://x/1","comentario":"A tese diz \\"dano moral presumido\\", e o acordao a aplica.","aprovada":true}\n' \
	>"$repo/data/ai/noticias_redigidas.jsonl"
# ★ A PAGINA CITA A NOTICIA, e por isso a pendencia e' ENRIQUECIMENTO.
#
# Sem o link no estoque a mesma linha cai na outra classe (`sem_pagina`), que
# NAO cobra tentativa — ver o caso logo abaixo. Medido em producao as 18:05: dos
# 8 comentarios aprovados fora do estoque, 4 tinham pagina citando a noticia
# (defeito real de enriquecimento) e 4 nao tinham pagina nenhuma; os dois grupos
# estavam sob o mesmo rotulo, e tres pecas do segundo grupo chegaram a PARADO
# por uma causa que nao era delas.
printf '{"intent_id":"not-a-1","fonte":"https://x/1","sections":[{"heading":"h","text":"corpo sem o comentario"}]}\n' \
	>"$repo/data/editorial/v2_pages/noticia-01.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
contem "$saida" "enriquecimento" "comentario aprovado cuja PAGINA existe tem de ser pendencia de enriquecimento"
nao_contem "$saida" "sem_pagina" "a pagina cita a noticia: classificar como sem_pagina esconderia um defeito real de enriquecimento"
# Agora o comentario ENTRA no corpo do estoque: a pendencia de enriquecimento some.
printf '{"intent_id":"not-a-1","fonte":"https://x/1","sections":[{"heading":"h","text":"Sobre X: A tese diz \\"dano moral presumido\\", e o acordao a aplica."}]}\n' \
	>"$repo/data/editorial/v2_pages/noticia-01.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
nao_contem "$saida" "enriquecimento" "comentario JA no estoque nao pode continuar pendente: a fila nunca esvaziaria"
# E a linha reprovada DESFAZ a aprovacao: peca recusada nao e' pendencia eterna.
printf '{"schema_version":"noticia_redigida_v1","link":"https://x/9","comentario":"OUTRA PROSA","aprovada":true}\n{"schema_version":"noticia_redigida_v1","link":"https://x/9","comentario":"OUTRA PROSA","aprovada":false}\n' \
	>>"$repo/data/ai/noticias_redigidas.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
nao_contem "$saida" "OUTRA PROSA" "linha mais nova reprovada tem de desfazer a aprovacao anterior do mesmo link"

# ★ SEM PAGINA PARA POUSAR: OUTRA CLASSE, E ELA NAO COBRA TENTATIVA.
#
# O gerador de noticias monta pagina por (orgao x dia) e recusa grupo com menos
# de 4 itens (o log da passada real diz "grupos abaixo de 4 itens: 81"). Para um
# comentario cuja noticia nao virou pagina nenhuma, NENHUMA retentativa cria a
# pagina: chamar isso de quarentena da peca leva a peca a PARADO por causa
# alheia, e foi o que aconteceu as 18:02 com tres pecas reais.
printf '{"schema_version":"noticia_redigida_v1","link":"https://x/sem-pagina","comentario":"PROSA SEM POUSO","aprovada":true}\n' \
	>>"$repo/data/ai/noticias_redigidas.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco 2>&1)"
contem "$saida" "SEM PAGINA PARA POUSAR" \
	"comentario cuja noticia nao tem pagina no estoque tem de sair na classe propria, com a causa"
contem "$saida" "nao cobra tentativa" \
	"a classe sem_pagina tem de declarar que nao cobra tentativa: sem isso a proxima sessao supoe quarentena"
# A LINHA DA PECA diz a classe, e e' por ela que a cobranca se decide. Asserir
# a CONTAGEM de acionaveis seria medir o cenario (que tem uma rota_nova
# legitima), e nao a classificacao -- foi a primeira versao deste caso.
linha_sem_pagina="$(grep -F "x/sem-pagina" <<<"$saida" | head -1)"
grep -qF "sem_pagina" <<<"$linha_sem_pagina" ||
	falha "a peca sem pagina saiu classificada como '$linha_sem_pagina': na classe acionavel ela viraria PARADO por causa que nao e' dela"

# ---------------------------------------------------------------------------
# 7.5 A REGUA DE SAIDA: 0, 3 e 1 nao se confundem
# ---------------------------------------------------------------------------
# A unit LE este numero para decidir se acorda o dono, entao ele e' contrato, e
# nao detalhe. `SuccessExitStatus=3` aceita SO o 3.
#
# Medido na primeira execucao real (17:45 e 17:52): a cadeia parou na etapa 4/9
# por `derived-body-repetition` (1.425 ocorrencias, todas em shard de acordao) e
# a unit alertou. O alerta estava CERTO -- o acervo inteiro esta bloqueado --, e
# o que estava errado era o rotulo do driver, que dizia "cadeia completou: sim".
veredito_de() {
	python3 - "$RAIZ/tools/publicar-estoque" "$1" "$2" "$3" "$4" <<'PYVEREDITO'
import importlib.util, sys
from importlib.machinery import SourceFileLoader
sys.dont_write_bytecode = True
caminho, parada, exit_cadeia, no_teto, quarentena = sys.argv[1:6]
spec = importlib.util.spec_from_loader("pe", SourceFileLoader("pe", caminho))
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)
codigo, motivo = pe.veredito(parada=parada, exit_da_cadeia=int(exit_cadeia),
                             no_teto=int(no_teto), em_quarentena=int(quarentena), teto=3)
print(f"{codigo}\t{motivo}")
PYVEREDITO
}
confere "$(veredito_de "" 0 0 0 | cut -f1)" "0" \
	"passada sem pendencia e sem parada tem de sair 0"
confere "$(veredito_de "" 0 0 2 | cut -f1)" "3" \
	"cadeia no fim com peca em quarentena ABAIXO do teto tem de sair 3 (desfecho previsto): sair 1 acorda o dono de meia em meia hora e o OnFailure vira ruido"
confere "$(veredito_de "" 0 1 2 | cut -f1)" "1" \
	"peca NO TETO tem de sair 1: e' o unico momento em que o sistema desistiu e o dono precisa decidir o refino"
confere "$(veredito_de "4/9 integridade (texto-repetido)" 1 0 3 | cut -f1)" "1" \
	"cadeia que PAROU em gate tem de sair 1, nunca 3: nada foi publicado e o acervo segue bloqueado"
confere "$(veredito_de "" 2 0 0 | cut -f1)" "2" \
	"defeito de processo (exit >= 2 da cadeia) tem de sobreviver ao veredito"
# E a ORDEM: teto vence parada e vence quarentena.
confere "$(veredito_de "4/9 integridade" 1 1 5 | cut -f1)" "1" \
	"com peca no teto E cadeia parada, o codigo tem de ser 1 pelas duas razoes"

# ---------------------------------------------------------------------------
# 8. Dado ilegivel e' NAO MEDIDO (exit 2), nunca "nada pendente" (exit 0)
# ---------------------------------------------------------------------------
printf 'isto nao e json\n' >>"$repo/data/editorial/published_manifest.jsonl"
python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo" --seco >/dev/null 2>&1
codigo=$?
[[ "$codigo" -eq 2 ]] || falha "manifesto ilegivel devolveu exit $codigo; tem de ser 2 (NAO MEDIDO), nunca 0"

# ---------------------------------------------------------------------------
# 9. A vedacao do `.git` esta nas units, e nao so no texto
# ---------------------------------------------------------------------------
for unit in wikijuridica-cerebro-publicar-noticias.service wikijuridica-cerebro-publicar-acordaos.service; do
	arquivo="$RAIZ/ops/systemd/$unit"
	[[ -f "$arquivo" ]] || {
		falha "unit ausente: ops/systemd/$unit"
		continue
	}
	texto="$(cat "$arquivo")"
	diretivas="$(so_diretivas "$texto")"
	# A VEDACAO DE FILESYSTEM SAIU EM 2026-09-16 (a politica mudou: o cerebro
	# commita). O que a substitui e' a PORTA UNICA, e o que esta bancada cobra
	# agora e' que nenhuma unit volte a declarar a linha -- ela tornaria a ordem
	# do dono inexequivel, porque commit legitimo precisa escrever em `.git`.
	nao_contem "$diretivas" "ReadOnlyPaths=/opt/wiki/.git" \
		"$unit voltou a vedar .git por filesystem: o commit restrito do cerebro falharia com EROFS e a ordem de 2026-09-16 ficaria inexequivel"
	contem "$diretivas" "PrivateTmp=false" \
		"$unit com /tmp privado nao compartilharia o flock da onda — duas passadas sobre os mesmos JSONL"
	# ★ `SuccessExitStatus` PODE EXISTIR, E SO PARA O 3 (precisado em 2026-09-16).
	#
	# A regra nao afrouxou: exit 1 continua sendo falha de verdade e continua
	# acordando o dono. O que a primeira execucao real mostrou e' que existe um
	# desfecho previsto — cadeia completa com peca em quarentena ABAIXO do teto —
	# que nao e' falha e vai ser o caso comum. Ele ganhou codigo proprio (3), e o
	# que esta bancada cobra agora e' que a unit aceite EXATAMENTE o 3: qualquer
	# lista que inclua 1 (ou `SIGTERM`, ou uma faixa) volta a apagar a diferenca
	# entre "nao tinha o que fazer" e "quebrou", que e' o defeito das vinte units.
	linha_sucesso="$(grep -E '^SuccessExitStatus=' <<<"$diretivas" || true)"
	if [[ -n "$linha_sucesso" ]]; then
		[[ "$linha_sucesso" == "SuccessExitStatus=3" ]] ||
			falha "$unit declara '$linha_sucesso': so o 3 (desfecho parcial previsto) pode ser aceito como sucesso — exit 1 e' falha de verdade neste publicador"
	fi
	contem "$diretivas" "OnFailure=wikijuridica-alerta@%N.service" "$unit sem alerta de falha"
	nao_contem "$diretivas" "ProtectHome=read-only" \
		"$unit com ProtectHome=read-only quebraria o cache do compilador Go em ~/.cache/go-build"
done

# ---------------------------------------------------------------------------
# 10. O bloqueio mede o GATILHO INTEIRO, o mesmo conjunto da etapa 5/9
# ---------------------------------------------------------------------------
# Portfolio sujo de OUTRO canal faz a cadeia quarentenar e sair. Se o bloqueio
# olhasse so o portfolio do proprio canal, `publicar-estoque` rodaria a cadeia,
# veria a peca nao entrar e cobraria tentativa -- em tres voltas o comentario do
# cerebro estaria PARADO por causa de um arquivo que nao e' dele.
repo_git="$tmp/repogit"
mkdir -p "$repo_git/ops" "$repo_git/content" "$repo_git/data/editorial/v2_pages" \
	"$repo_git/data/editorial/portfolio_v2" "$repo_git/data/ai" "$repo_git/data/ops"
cat >"$repo_git/ops/produtores-de-pagina.jsonl" <<'REG2'
{"canal":"noticias","cmd":"./cmd/gn","shard":"data/editorial/v2_pages/noticia-01.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-01.jsonl","gatilho":"onda-diaria","limite_env":"A","limite_padrao":40}
{"canal":"leis","cmd":"./cmd/gl","shard":"data/editorial/v2_pages/lei-01.jsonl","portfolio":"data/editorial/portfolio_v2/lei-01.jsonl","gatilho":"onda-diaria","limite_env":"B","limite_padrao":30}
REG2
printf '{"schema_version":"cerebro_publicacao_v1","handle_do_autor":"x","modelo":"m","teto_por_execucao":5,"teto_de_tentativas_por_peca":2}\n' \
	>"$repo_git/content/cerebro_publicacao.json"
printf '{"intent_id":"n-1"}\n' >"$repo_git/data/editorial/v2_pages/noticia-01.jsonl"
printf '{"unique_intent_id":"n-1"}\n' >"$repo_git/data/editorial/published_manifest.jsonl"
printf '{"intent_id":"n-1"}\n' >"$repo_git/data/editorial/portfolio_v2/noticia-01.jsonl"
printf '{"intent_id":"l-1"}\n' >"$repo_git/data/editorial/portfolio_v2/lei-01.jsonl"
(
	cd "$repo_git" || exit 1
	git init -q .
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base >/dev/null 2>&1
) || falha "nao consegui montar o cenario com historico"
# Agora suja o portfolio do canal ALHEIO.
printf '{"intent_id":"l-2"}\n' >>"$repo_git/data/editorial/portfolio_v2/lei-01.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo_git" --seco 2>&1)"
contem "$saida" "BLOQUEADO" \
	"portfolio sujo de outro canal tem de BLOQUEAR: o gate de pareamento le o diretorio inteiro"
contem "$saida" "lei-01.jsonl" "o bloqueio tem de NOMEAR o arquivo que espera commit"

# ★ E O ESCOPO E' TODO GATILHO, nao so o da passada — medido em producao.
#
# Uma passada de NOTICIAS (gatilho `onda-diaria`) reprovou no 6/9 com "7539
# intencao(oes) existem no disco mas NAO no commit pai", e as 7.539 eram de
# ACORDAOS (gatilho `publicador-cerebro`). `check-v2-portfolio-pairing` le
# `data/editorial/v2_pages` INTEIRO: ele nao conhece gatilho. Um bloqueio com
# escopo menor que o do gate que ele antecipa manda a cadeia rodar para morrer.
cat >>"$repo_git/ops/produtores-de-pagina.jsonl" <<'REG3'
{"canal":"acordaos","cmd":"./cmd/ga","shard":"data/editorial/v2_pages/acordao-01.jsonl","portfolio":"data/editorial/portfolio_v2/acordao-01.jsonl","gatilho":"publicador-cerebro","limite_env":"C","limite_padrao":30}
REG3
printf '{"intent_id":"a-1"}\n' >"$repo_git/data/editorial/portfolio_v2/acordao-01.jsonl"
(
	cd "$repo_git" || exit 1
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base2 >/dev/null 2>&1
) || falha "nao consegui commitar o cenario de gatilho cruzado"
printf '{"intent_id":"a-2"}\n' >>"$repo_git/data/editorial/portfolio_v2/acordao-01.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo_git" --seco 2>&1)"
contem "$saida" "acordao-01.jsonl" \
	"portfolio sujo de OUTRO GATILHO tem de bloquear a passada de noticias: o gate de pareamento nao conhece gatilho"

# ★ PORTFOLIO ESTAGIADO E NAO COMMITADO TAMBEM E' "AGUARDANDO COMMIT".
#
# `git diff` compara worktree contra INDICE: depois que outra sessao estagia, os
# dois sao iguais e o arquivo some do radar — e `ls-files --others` so ve o nao
# rastreado. O estado ficava invisivel justamente para a funcao que existe para
# ve-lo, e a passada seguia para reprovar no 6/9, em retomada. Medido em
# producao nesta data: `stj-acordao-derivado-02..08.jsonl` estavam `A` no indice,
# estagiados por outra frente.
(
	cd "$repo_git" || exit 1
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base3 >/dev/null 2>&1
	printf '{"intent_id":"l-9"}\n' >>data/editorial/portfolio_v2/lei-01.jsonl
	git -c user.email=b@b -c user.name=b add data/editorial/portfolio_v2/lei-01.jsonl >/dev/null 2>&1
) || falha "nao consegui montar o cenario de portfolio estagiado"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo_git" --seco 2>&1)"
contem "$saida" "BLOQUEADO" \
	"portfolio ESTAGIADO e nao commitado nao bloqueou: a passada roda para reprovar no 6/9 e volta em retomada eterna"
contem "$saida" "lei-01.jsonl" "o bloqueio por portfolio estagiado tem de nomear o arquivo"

# E a familia do portfolio usa a MESMA regua: ordinal UNICODE nao e' da familia.
printf '{"intent_id":"l-u"}\n' >"$repo_git/data/editorial/portfolio_v2/noticia-٠١.jsonl"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$repo_git" --seco 2>&1)"
nao_contem "$saida" "٠١" "o bloqueio nomeou portfolio com ordinal UNICODE: regua divergente da cadeia"

# ---------------------------------------------------------------------------
# 11. Tentativa so se cobra de passada que chegou ao fim
# ---------------------------------------------------------------------------
sonda_completou() {
	python3 - "$RAIZ/tools/publicar-estoque" "$1" "$2" <<'PYCOMPLETOU'
import importlib.util, sys
caminho, raiz, rotulo = sys.argv[1:4]
spec = importlib.util.spec_from_loader(
    "pe", importlib.machinery.SourceFileLoader("pe", caminho))
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)
modulo.RAIZ = raiz
print("sim" if modulo.passada_completou(rotulo) else "nao")
PYCOMPLETOU
}
printf '{"data":"2026-09-16","rotulo":"r","escopo":"quarentena","resultado":"ok"}\n' \
	>"$repo_git/data/ops/daily_content_runs.jsonl"
[[ "$(sonda_completou "$repo_git" r)" == "nao" ]] ||
	falha "passada quarentenada foi lida como completa: a peca levaria tentativa por culpa alheia"
printf '{"data":"2026-09-16","rotulo":"r","escopo":"completa","resultado":"ok"}\n' \
	>>"$repo_git/data/ops/daily_content_runs.jsonl"
[[ "$(sonda_completou "$repo_git" r)" == "sim" ]] ||
	falha "passada completa nao foi reconhecida: nenhuma tentativa seria cobrada nunca, e o teto viraria letra morta"
[[ "$(sonda_completou "$repo_git" outro-rotulo)" == "nao" ]] ||
	falha "rotulo sem linha nenhuma foi lido como completo"

# ★ O CRITERIO DE COBRANCA E' `gerou`, E NAO "a cadeia chegou ao fim" (2026-09-16).
#
# Medido as 17:52: a cadeia PAROU na 4/9 (`derived-body-repetition`, 1.425
# ocorrencias em shard de acordao) e a etapa 2/9 ja tinha concluido -- `noticias
# ok gravado: ... (63 paginas)`. A peca de noticia FOI tentada pelo gerador dela
# e nao entrou: a tentativa e' legitima. Se o critero fosse "chegou ao fim",
# nenhuma peca seria cobrada enquanto um gate global parasse a cadeia, e o teto
# viraria letra morta -- laco silencioso. E se toda parada cobrasse, a peca cujo
# gerador nem rodou seria punida por culpa alheia.
printf '{"data":"2026-09-16","rotulo":"g","escopo":"parou_em_etapa","parou_em":"4/9 integridade","gerou":true,"resultado":"parcial","falhas":["texto-repetido"]}\n' \
	>"$repo_git/data/ops/daily_content_runs.jsonl"
[[ "$(sonda_completou "$repo_git" g)" == "sim" ]] ||
	falha "cadeia parada em gate COM o gerador concluido nao cobrou tentativa: enquanto o gate global durar, nenhuma peca chegaria ao teto e o refino humano nunca seria chamado"
printf '{"data":"2026-09-16","rotulo":"h","escopo":"parou_em_etapa","parou_em":"1/9 coleta","gerou":false,"resultado":"parcial","falhas":["coleta"]}\n' \
	>>"$repo_git/data/ops/daily_content_runs.jsonl"
[[ "$(sonda_completou "$repo_git" h)" == "nao" ]] ||
	falha "cadeia parada ANTES de gerar cobrou tentativa: a peca seria punida por uma passada que nem chegou ao gerador dela"
# E a parada tem de ser NOMEADA: "completou: sim" para cadeia parada na 4/9 foi o
# que fez o journal desta data ser lido como alarme falso.
sonda_parada() {
	python3 - "$RAIZ/tools/publicar-estoque" "$1" "$2" <<'PYPARADA'
import importlib.util, sys
from importlib.machinery import SourceFileLoader
sys.dont_write_bytecode = True
caminho, raiz, rotulo = sys.argv[1:4]
spec = importlib.util.spec_from_loader("pe", SourceFileLoader("pe", caminho))
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)
modulo.RAIZ = raiz
print(modulo.parada_da_cadeia(rotulo) or "(vazio)")
PYPARADA
}
confere "$(sonda_parada "$repo_git" g)" "4/9 integridade (texto-repetido)" \
	"a parada da cadeia tem de sair com etapa E rotulo da falha: sem os dois, quem le o journal procura o defeito no lugar errado"
printf '{"data":"2026-09-16","rotulo":"i","escopo":"completa","gerou":true,"resultado":"ok","falhas":[]}\n' \
	>>"$repo_git/data/ops/daily_content_runs.jsonl"
confere "$(sonda_parada "$repo_git" i)" "(vazio)" \
	"passada completa nao pode reportar parada nenhuma"
# A CADEIA GRAVA OS DOIS CAMPOS. Sem isto o driver leria `gerou` de ninguem e
# cairia para sempre no fallback do escopo.
contem "$(cat "$RAIZ/tools/run-daily-content")" '"gerou": gerou == "1"' \
	"a cadeia parou de gravar o campo gerou: o criterio de cobranca voltaria a ser o escopo, que mente em parada por gate"
contem "$(cat "$RAIZ/tools/run-daily-content")" 'escopo=parou_em_etapa' \
	"a cadeia voltou a gravar completa para toda parada: e o campo-proxy que fez o publicador dizer cadeia-completou-sim numa parada de 4/9"

# ---------------------------------------------------------------------------
# 12. Peca PARADA tem destinatario
# ---------------------------------------------------------------------------
# Fila com produtor e sem leitor e' o defeito medido em `v2_rewrite_queue.jsonl`
# (3.101 paginas vivas esperando, zero reescritores). Aqui o leitor e' o canal
# de alerta do dono.
fonte_pe="$(cat "$RAIZ/tools/publicar-estoque")"
# A ASSERCAO E' SOBRE CHAMADA EM POSICAO DE COMANDO, nao sobre a string: um
# `_ = (chave_parado, ...)` mantem o texto e nao alerta ninguem. Foi o mutante
# que sobreviveu na primeira rodada desta bancada.
# As DUAS chamadas se cobram separadamente. Na primeira rodada a assercao casava
# qualquer `avisa_dono(chave_parado`, e o mutante que matava a ABERTURA sobrevivia
# porque a linha da RESOLUCAO continuava casando — assercao que confunde os dois
# lados do alarme nao cobre nenhum.
if ! grep -qE '^[[:space:]]+avisa_dono\(chave_parado, "alta",' "$RAIZ/tools/publicar-estoque"; then
	falha "peca PARADA nao ABRE alerta ao dono: fila com produtor e sem leitor e' o defeito de v2_rewrite_queue"
fi
if ! grep -qE '^[[:space:]]+avisa_dono\(chave_parado, "media",' "$RAIZ/tools/publicar-estoque"; then
	falha "sem peca parada o alerta nao e' RESOLVIDO: alerta que ninguem fecha vira ruido que se aprende a ignorar"
fi
contem "$fonte_pe" 'resolvido=True' "o alerta tem de FECHAR quando nao ha mais peca parada"
contem "$fonte_pe" '"nao_avaliados"' "o ledger tem de separar o que nao entrou do que nem foi avaliado"

# ---------------------------------------------------------------------------
# 13. A copia de preservacao nao pode sobrescrever a da passada anterior
# ---------------------------------------------------------------------------
# O publicador roda varias vezes ao dia. Um nome so com a data faria a segunda
# passada apagar a copia da primeira -- preservacao que apaga o que preservou, e
# delecao e' vedada pelo contrato de poderes.
if ! grep -qE 'PRESERVADO=.*%H%M%S' "$RAIZ/tools/run-daily-content"; then
	falha "a copia de preservacao do --sem-git nao carrega hora no nome: duas passadas no mesmo dia se sobrescrevem"
fi
if ! grep -qE 'inicio\.strftime\("%Y%m%d-%H%M%S"\)' "$RAIZ/tools/publicar-estoque"; then
	falha "a copia de preservacao de publicar-estoque nao carrega hora no nome"
fi

# ---------------------------------------------------------------------------
# 14. A PORTA UNICA recusa cada proibido, pela PROPRIA trava
# ---------------------------------------------------------------------------
# Em systemd os hooks do CLI do Claude Code NAO EXISTEM: eles interceptam a
# sessao, nao o sistema. Se a recusa viesse do hook, a trava nao existiria onde
# ela mais importa. Por isso cada caso abaixo tem de sair 2 com o CODIGO nomeado
# pelo proprio wrapper.
recusa_do_wrapper() {
	local tipo="$1" caminho="$2" codigo_esperado="$3" nome="$4" saida codigo
	saida="$(python3 "$RAIZ/tools/cerebro-commitar" --tipo "$tipo" --rotulo bancada --seco -- "$caminho" 2>&1)"
	codigo=$?
	if [[ "$codigo" -ne 2 ]]; then
		falha "$nome: exit $codigo, esperado 2 (recusa da porta)"
		return
	fi
	grep -qF -e "RECUSADO [$codigo_esperado]" <<<"$saida" ||
		falha "$nome: recusou, mas com codigo diferente de $codigo_esperado -- codigo que nomeia a causa errada manda a proxima sessao procurar no lugar errado: $(tail -1 <<<"$saida")"
}
recusa_do_wrapper portfolio data/editorial/v2_pages/noticias-oficiais-01.jsonl \
	fora_da_allowlist "shard pedido como portfolio (tipo trocado)"
recusa_do_wrapper paginas data/editorial \
	diretorio "estagiar DIRETORIO, que ja varreu trabalho de outra sessao tres vezes"
recusa_do_wrapper paginas ../etc/passwd \
	travessia "pathspec saindo da arvore"
recusa_do_wrapper paginas data/editorial/v2_pages/../../../etc/hosts \
	travessia "pathspec com .."
recusa_do_wrapper paginas content/pages.json \
	fora_da_allowlist "arquivo real do repo, fora da allowlist"
recusa_do_wrapper paginas data/editorial/v2_pages/nao-existe-99.jsonl \
	remocao "arquivo ausente: commitar a ausencia seria remocao"
# SYMLINK: o caso esta mais abaixo, no `cenario_allow`, e NAO aqui.
#
# A primeira versao deste caso criava o symlink dentro de
# `data/editorial/v2_pages/` DE PRODUCAO e o apagava com `rm -f`. Tres defeitos
# num so: outra sessao fazendo `add` por diretorio nesse intervalo varreria o
# link para dentro de um commit; bancada interrompida no meio deixaria o link
# para tras; e apagar arquivo do repo e' exatamente a especie de ato que a
# vedacao reafirmada proibe. Bancada nao escreve em producao — nem para provar
# que a porta recusa.
# ★ PERTINENCIA A CONJUNTO, E NAO PREFIXO — o caso que so um cenario proprio
# consegue distinguir, e que deixou um mutante vivo na primeira rodada.
#
# Contra a allowlist de producao, `startswith(dirname)` e `in conjunto` recusam
# exatamente as mesmas coisas: nenhum caso tinha um arquivo VIZINHO do shard
# registrado. Aqui o cenario poe `noticia-01.jsonl` (registrado) ao lado de
# `noticia-01.jsonl.bak` e `noticia-99.jsonl` (nao registrados) — por prefixo os
# dois passariam.
cenario_allow="$tmp/allow"
mkdir -p "$cenario_allow/ops" "$cenario_allow/data/editorial/v2_pages" \
	"$cenario_allow/data/editorial/portfolio_v2"
cat >"$cenario_allow/ops/produtores-de-pagina.jsonl" <<'REGALLOW'
{"canal":"noticias","cmd":"./cmd/gn","shard":"data/editorial/v2_pages/noticia-01.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-01.jsonl","gatilho":"onda-diaria","limite_env":"A","limite_padrao":40}
REGALLOW
printf '{"intent_id":"n-1"}\n' >"$cenario_allow/data/editorial/v2_pages/noticia-01.jsonl"
printf 'lixo\n' >"$cenario_allow/data/editorial/v2_pages/noticia-01.jsonl.bak"
printf 'lixo\n' >"$cenario_allow/data/editorial/v2_pages/noticia-99.jsonl"
printf '{"intent_id":"n-1"}\n' >"$cenario_allow/data/editorial/portfolio_v2/noticia-01.jsonl"
valida_no_cenario() {
	python3 "$RAIZ/tools/cerebro-commitar" --tipo paginas --rotulo bancada --seco \
		--raiz "$cenario_allow" -- "$1" 2>&1
	return $?
}
saida="$(valida_no_cenario data/editorial/v2_pages/noticia-01.jsonl)"
codigo=$?
[[ "$codigo" -eq 0 ]] || falha "o shard REGISTRADO foi recusado no cenario (exit $codigo): $(tail -1 <<<"$saida")"
saida="$(valida_no_cenario data/editorial/v2_pages/noticia-01.jsonl.bak)"
codigo=$?
if [[ "$codigo" -ne 2 ]]; then
	falha "noticia-01.jsonl.bak passou (exit $codigo): a allowlist esta conferindo PREFIXO, e nao pertinencia a conjunto — vizinho do shard registrado entraria no commit"
else
	grep -qF -e "RECUSADO [fora_da_allowlist]" <<<"$saida" ||
		falha "noticia-01.jsonl.bak recusado pelo codigo errado: $(tail -1 <<<"$saida")"
fi
# ★ `noticia-99.jsonl` PASSA, E ISSO E' A ROTACAO FUNCIONANDO, nao um furo.
#
# Minha expectativa inicial aqui estava ERRADA e a bancada a corrigiu: o gerador
# abre `-02`, `-03`... quando o `-01` enche, e uma allowlist que so aceitasse o
# ordinal declarado no registro faria o publicador parar de commitar na primeira
# rotacao. O conjunto e' a FAMILIA `<prefixo>-NN.jsonl` do produtor declarado, e
# a fronteira e' a mesma que `alvos_do_registro` ja usa para decidir o que a onda
# commita -- dois instrumentos com a MESMA regua, que e' o que este repositorio
# exige de duas medidas do mesmo fato.
saida="$(valida_no_cenario data/editorial/v2_pages/noticia-99.jsonl)"
codigo=$?
[[ "$codigo" -eq 0 ]] ||
	falha "noticia-99.jsonl foi recusado (exit $codigo): a rotacao de shard pararia de ser commitavel a partir do -02, e o publicador travaria na primeira rotacao"

# SYMLINK, no cenario e nunca em producao. O nome escolhido esta DENTRO da
# familia de rotacao aceita logo acima, entao a allowlist o aprovaria pelo nome:
# quem recusa tem de ser a conferencia de symlink, e ela roda ANTES do realpath.
ln -sfn "$cenario_allow/data/editorial/v2_pages/noticia-01.jsonl" \
	"$cenario_allow/data/editorial/v2_pages/noticia-98.jsonl" ||
	falha "nao consegui montar o cenario de symlink"
saida="$(valida_no_cenario data/editorial/v2_pages/noticia-98.jsonl)"
codigo=$?
if [[ "$codigo" -ne 2 ]]; then
	falha "symlink dentro da familia de rotacao passou (exit $codigo): o commit gravaria um blob de link no lugar do conteudo"
else
	grep -qF -e "RECUSADO [symlink]" <<<"$saida" ||
		falha "symlink recusado pelo codigo errado -- a conferencia de symlink tem de vir ANTES do realpath, senao o link some na canonicalizacao: $(tail -1 <<<"$saida")"
fi

# ★ PARIDADE DE REGUA ENTRE A PORTA (Python) E A CADEIA (bash).
#
# A familia de rotacao esta escrita em cinco lugares: o glob
# `-[0-9][0-9].jsonl` de `alvos_do_registro` (tools/run-daily-content), dois
# regexes em `tools/publicar-estoque` e dois em `tools/cerebro-commitar`. Enquanto
# houver mais de uma implementacao, a paridade se MEDE — e ela ja estava
# quebrada: `\d` do Python casa digito UNICODE, entao `noticia-٠١.jsonl` (indo-
# arabico, medido: `int("٠١") == 1`) entrava na allowlist da porta e NUNCA no
# glob do bash. Porta que aceita caminho que a cadeia jamais escreve e'
# superficie a mais.
printf 'lixo\n' >"$cenario_allow/data/editorial/v2_pages/noticia-٠١.jsonl"
saida="$(valida_no_cenario data/editorial/v2_pages/noticia-٠١.jsonl)"
codigo=$?
if [[ "$codigo" -ne 2 ]]; then
	falha "ordinal com digito UNICODE passou na allowlist (exit $codigo): a porta aceita o que a cadeia nunca escreve -- use [0-9]{2}, nunca \\d\\d"
else
	grep -qF -e "RECUSADO [fora_da_allowlist]" <<<"$saida" ||
		falha "ordinal com digito UNICODE recusado pelo codigo errado: $(tail -1 <<<"$saida")"
fi
# E o ordinal DECLARADO no registro tambem passa pela mesma regua: registro com
# ordinal que a cadeia nao sabe globar e' ILEGIVEL, nunca "familia derivada em
# silencio". Sem isto, a porta e o driver aceitariam um registro que faria a onda
# nao commitar nada — e ninguem saberia por que.
reg_unicode="$tmp/regunicode"
mkdir -p "$reg_unicode/ops" "$reg_unicode/content" "$reg_unicode/data/editorial/v2_pages" \
	"$reg_unicode/data/editorial/portfolio_v2" "$reg_unicode/data/ai" "$reg_unicode/data/ops"
# UM MARCADOR POR CENARIO: so o SHARD tem ordinal invalido aqui; o portfolio e'
# valido de proposito. Com os dois invalidos, a funcao do portfolio levantava a
# MESMA frase e um mutante do shard sobrevivia escondido atras dela — foi o que
# aconteceu nesta bancada, e e' fixture, nao predicado.
cat >"$reg_unicode/ops/produtores-de-pagina.jsonl" <<'REGU'
{"canal":"noticias","cmd":"./cmd/gn","shard":"data/editorial/v2_pages/noticia-٠١.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-01.jsonl","gatilho":"onda-diaria","limite_env":"A","limite_padrao":40}
REGU
printf '{"schema_version":"cerebro_publicacao_v1","handle_do_autor":"x","modelo":"m","teto_por_execucao":5}\n' \
	>"$reg_unicode/content/cerebro_publicacao.json"
printf '{"intent_id":"u-1"}\n' >"$reg_unicode/data/editorial/v2_pages/noticia-٠١.jsonl"
printf '{"intent_id":"u-1"}\n' >"$reg_unicode/data/editorial/portfolio_v2/noticia-01.jsonl"
: >"$reg_unicode/data/editorial/published_manifest.jsonl"
(
	cd "$reg_unicode" || exit 1
	git init -q .
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base >/dev/null 2>&1
) || falha "nao consegui montar o cenario de shard com ordinal invalido"
saida="$(python3 "$RAIZ/tools/cerebro-commitar" --tipo paginas --rotulo bancada --seco \
	--raiz "$reg_unicode" -- data/editorial/v2_pages/noticia-٠١.jsonl 2>&1)"
codigo=$?
[[ "$codigo" -eq 2 ]] ||
	falha "a porta aceitou registro com ordinal que a cadeia nao globa (exit $codigo): a onda nao commitaria nada e a causa ficaria invisivel"
grep -qF -e "RECUSADO [registro_ilegivel]" <<<"$saida" ||
	falha "registro com ordinal UNICODE recusado pelo codigo errado: $(tail -1 <<<"$saida")"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$reg_unicode" --seco 2>&1)"
codigo=$?
[[ "$codigo" -eq 2 ]] ||
	falha "o driver devolveu exit $codigo para registro com ordinal que a cadeia nao globa; tem de ser 2 (NAO MEDIDO)"
# A MENSAGEM, e nao so o exit: com `\d\d` no search o driver tambem sai 2, porem
# por "nenhum shard existente" — causa errada, que manda procurar no diretorio em
# vez de no registro. Um mutante sobreviveu exatamente assim nesta bancada.
contem "$saida" "shard 'data/editorial/v2_pages/noticia-٠١.jsonl'" \
	"o driver saiu 2 pela causa errada: o SHARD com ordinal invalido tem de ser reprovado NO REGISTRO, nao virar familia vazia"
contem "$saida" "nao termina em -NN.jsonl" \
	"a reprovacao nao diz o que esta errado no registro"

# O MESMO para o campo `portfolio`, que tem funcao propria e regua propria: com o
# shard valido, quem responde e' `portfolios_aguardando_commit`.
reg_uni_port="$tmp/regunipor"
mkdir -p "$reg_uni_port/ops" "$reg_uni_port/content" "$reg_uni_port/data/editorial/v2_pages" \
	"$reg_uni_port/data/editorial/portfolio_v2" "$reg_uni_port/data/ai" "$reg_uni_port/data/ops"
cat >"$reg_uni_port/ops/produtores-de-pagina.jsonl" <<'REGUP'
{"canal":"noticias","cmd":"./cmd/gn","shard":"data/editorial/v2_pages/noticia-01.jsonl","portfolio":"data/editorial/portfolio_v2/noticia-٠١.jsonl","gatilho":"onda-diaria","limite_env":"A","limite_padrao":40}
REGUP
printf '{"schema_version":"cerebro_publicacao_v1","handle_do_autor":"x","modelo":"m","teto_por_execucao":5}\n' \
	>"$reg_uni_port/content/cerebro_publicacao.json"
printf '{"intent_id":"p-1"}\n' >"$reg_uni_port/data/editorial/v2_pages/noticia-01.jsonl"
printf '{"intent_id":"p-1"}\n' >"$reg_uni_port/data/editorial/portfolio_v2/noticia-٠١.jsonl"
: >"$reg_uni_port/data/editorial/published_manifest.jsonl"
(
	cd "$reg_uni_port" || exit 1
	git init -q .
	git -c user.email=b@b -c user.name=b add -A >/dev/null 2>&1
	git -c user.email=b@b -c user.name=b commit -q -m base >/dev/null 2>&1
) || falha "nao consegui montar o cenario de portfolio com ordinal invalido"
saida="$(python3 "$RAIZ/tools/publicar-estoque" --canal noticias --raiz "$reg_uni_port" --seco 2>&1)"
codigo=$?
[[ "$codigo" -eq 2 ]] ||
	falha "portfolio com ordinal que a cadeia nao globa devolveu exit $codigo: a passada seguiria sem NUNCA conseguir commitar o portfolio"
contem "$saida" "nao termina em -NN.jsonl" \
	"a reprovacao do portfolio invalido tem de nomear o registro: sem isso a familia vira vazia em silencio e o bloqueio nunca dispara"

# E a cadeia, sobre o MESMO diretorio, tambem nao o enxerga.
mkdir -p "$cenario_allow/tools"
cp "$RAIZ/tools/listar-produtores-de-pagina" "$cenario_allow/tools/listar-produtores-de-pagina"
alvos_bash="$(cd "$cenario_allow" && GATILHO=onda-diaria bash -c "$corpo"'; alvos_do_registro shard' 2>&1)"
nao_contem "$alvos_bash" "٠١" "o glob do bash passou a enxergar ordinal UNICODE: as duas reguas divergiram para o outro lado"
contem "$alvos_bash" "noticia-01.jsonl" "a cadeia perdeu o shard registrado no cenario de paridade"
contem "$alvos_bash" "noticia-99.jsonl" "a cadeia nao enxerga a rotacao que a porta aceita: divergencia entre as duas reguas"
nao_contem "$alvos_bash" "noticia-01.jsonl.bak" "o glob do bash passou a varrer vizinho fora da familia"
# `--raiz` sem `--seco` NAO pode existir: seria commitar num repositorio alheio.
python3 "$RAIZ/tools/cerebro-commitar" --tipo paginas --rotulo b --raiz "$cenario_allow" \
	-- data/editorial/v2_pages/noticia-01.jsonl >/dev/null 2>&1 &&
	falha "--raiz sem --seco foi aceito: a porta escreveria historico fora deste repositorio"

# E NAO EXISTE SUPERFICIE para subcomando destrutivo: `--tipo` e' um conjunto
# fechado, entao pedir `reset` nem chega a ser um pedido.
python3 "$RAIZ/tools/cerebro-commitar" --tipo reset --rotulo b --seco -- x >/dev/null 2>&1 &&
	falha "a porta aceitou --tipo reset: subcomando destrutivo tem de ser INEXPRIMIVEL, nao proibido por lista"
for destrutivo in reset revert checkout restore stash clean rebase "cherry-pick" push "filter-branch" gc rm; do
	if grep -qE "^[[:space:]]*(subprocess\.run\(\[GIT|git)\(?\"?$destrutivo" "$RAIZ/tools/cerebro-commitar"; then
		falha "a porta invoca o subcomando destrutivo '$destrutivo'"
	fi
done

# A CONFERENCIA DE REMOCAO RODA DUAS VEZES: ANTES DE ESTAGIAR E ANTES DE COMMITAR.
#
# Depois de estagiar, porque um arquivo pode existir no disco na validacao e
# ainda entrar no indice como `D` (outra sessao o removeu no meio).
# Antes de estagiar, pelo motivo MEDIDO no caso logo abaixo: o indice e'
# compartilhado, e o commit escopado por pathspec leva junto o `D` que ja
# estivesse estagiado para um caminho DENTRO daquele mesmo pathspec.
ordem_do_wrapper="$(grep -nE '^ *(estagiar = sob_lock|nenhuma_remocao\(caminhos, momento=|commitar = sob_lock)' "$RAIZ/tools/cerebro-commitar" | cut -d: -f1 | tr '\n' ' ')"
read -r linha_antes linha_estagiar linha_depois linha_commit <<<"$ordem_do_wrapper"
if [[ -z "${linha_commit:-}" ]] || ((linha_antes >= linha_estagiar)) ||
	((linha_estagiar >= linha_depois)) || ((linha_depois >= linha_commit)); then
	falha "a porta nao confere remocao ANTES de estagiar E entre estagiar e commitar (linhas: '$ordem_do_wrapper'): commit que remove arquivo passaria"
fi

# ★ POR QUE A CONFERENCIA DE ANTES EXISTE: O GIT LEVA O `D` DO VIZINHO.
#
# Medido num repositorio de rascunho, aqui, a cada rodada -- e nao afirmado de
# memoria. Se um dia o git mudar esse comportamento, este caso avisa; enquanto
# ele valer, a pre-conferencia e' obrigatoria. O escopo tambem se mede: o `D`
# so entra quando o caminho removido esta DENTRO do pathspec pedido, que e'
# exatamente o conjunto que `nenhuma_remocao` inspeciona.
rascunho="$tmp/git-leva-o-d"
mkdir -p "$rascunho/data/editorial/v2_pages"
(
	cd "$rascunho" || exit 1
	export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
	/usr/bin/git init -q . && /usr/bin/git config user.email t@t && /usr/bin/git config user.name t || exit 1
	printf 'a\n' >data/editorial/v2_pages/a.jsonl
	printf 'b\n' >data/editorial/v2_pages/b.jsonl
	/usr/bin/git add data/editorial/v2_pages/a.jsonl data/editorial/v2_pages/b.jsonl || exit 1
	printf 'inicial\n' >msg1.txt
	/usr/bin/git commit -q -F msg1.txt || exit 1
	# outra sessao estagia a remocao de b.jsonl
	/usr/bin/git rm -q --cached data/editorial/v2_pages/b.jsonl >/dev/null || exit 1
	rm -f data/editorial/v2_pages/b.jsonl
	printf 'a2\n' >data/editorial/v2_pages/a.jsonl
	/usr/bin/git add data/editorial/v2_pages/a.jsonl || exit 1
	printf 'porta\n' >msg2.txt
	/usr/bin/git commit -q -F msg2.txt -- data/editorial/v2_pages/a.jsonl data/editorial/v2_pages/b.jsonl || exit 1
) >/dev/null 2>&1 || falha "nao consegui montar o rascunho que mede o comportamento do git"
if [[ -d "$rascunho/.git" ]]; then
	dentro="$(/usr/bin/git -C "$rascunho" show --name-status --format= HEAD | grep -c '^D')"
	[[ "$dentro" -eq 1 ]] ||
		falha "o rascunho nao reproduziu o fato que motiva a pre-conferencia (D no commit: $dentro): confira se o git mudou de comportamento antes de mexer na porta"
fi

# E a pre-conferencia RECUSA esse caso -- a funcao rodada sobre o indice real do
# rascunho, sem `--raiz` (que exige `--seco` e nem chega a estagiar).
if [[ -d "$rascunho/.git" ]]; then
	/usr/bin/git -C "$rascunho" rm -q --cached data/editorial/v2_pages/a.jsonl >/dev/null 2>&1
	recusou="$(RASCUNHO="$rascunho" RAIZ_BANCADA="$RAIZ" python3 - <<'PYREMOCAO'
import importlib.util, os, sys
from importlib.machinery import SourceFileLoader
sys.dont_write_bytecode = True
alvo = os.path.join(os.environ["RAIZ_BANCADA"], "tools", "cerebro-commitar")
spec = importlib.util.spec_from_loader("porta", SourceFileLoader("porta", alvo))
porta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(porta)
porta.RAIZ = os.environ["RASCUNHO"]
try:
    porta.nenhuma_remocao(["data/editorial/v2_pages/a.jsonl"], momento="antes de estagiar")
except porta.Recusa as recusa:
    print(f"RECUSOU {recusa.codigo} {recusa.detalhe}")
else:
    print("ACEITOU")
PYREMOCAO
	)"
	grep -qF -e "RECUSOU remocao" <<<"$recusou" ||
		falha "a conferencia de remocao aceitou um D ja estagiado por outra sessao: o commit da porta levaria a remocao junto -- $recusou"
	grep -qF -e "antes de estagiar" <<<"$recusou" ||
		falha "a recusa nao diz em QUAL momento recusou: a proxima sessao nao saberia se o D chegou antes ou depois do add -- $recusou"
fi

# ★ A LEITURA DA PORTA NAO PODE ESCREVER O INDICE COMPARTILHADO.
#
# `git diff --quiet -- <caminhos>` reescreve `.git/index` mesmo com
# GIT_OPTIONAL_LOCKS=0 (medido em git 2.39.5): para o diff do worktree o refresh
# nao e' opcional. `git status --porcelain` COM a variavel nao reescreve. Como o
# indice deste repositorio e' compartilhado entre sessoes, a porta le por
# `status`. Este caso mede o carimbo do indice antes e depois de `ha_mudanca`.
if [[ -d "$rascunho/.git" ]]; then
	printf 'a3\n' >"$rascunho/data/editorial/v2_pages/a.jsonl"
	/usr/bin/git -C "$rascunho" add data/editorial/v2_pages/a.jsonl >/dev/null 2>&1
	touch -d '2011-01-01' "$rascunho/data/editorial/v2_pages/a.jsonl"
	carimbo_antes="$(stat -c '%z' "$rascunho/.git/index")"
	leitura="$(RASCUNHO="$rascunho" RAIZ_BANCADA="$RAIZ" python3 - <<'PYLEITURA'
import importlib.util, os, sys
from importlib.machinery import SourceFileLoader
sys.dont_write_bytecode = True
alvo = os.path.join(os.environ["RAIZ_BANCADA"], "tools", "cerebro-commitar")
spec = importlib.util.spec_from_loader("porta", SourceFileLoader("porta", alvo))
porta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(porta)
porta.RAIZ = os.environ["RASCUNHO"]
print("mudou" if porta.ha_mudanca(["data/editorial/v2_pages/a.jsonl"]) else "limpo")
PYLEITURA
	)"
	carimbo_depois="$(stat -c '%z' "$rascunho/.git/index")"
	[[ "$leitura" == "mudou" ]] ||
		falha "a porta nao viu a mudanca no arquivo estagiado ($leitura): commit legitimo seria descartado como 'sem novidade'"
	[[ "$carimbo_antes" == "$carimbo_depois" ]] ||
		falha "a leitura da porta REESCREVEU .git/index ($carimbo_antes -> $carimbo_depois): o indice e' compartilhado, e leitura que escreve disputa com o add de outra sessao"
fi

# ---------------------------------------------------------------------------
# 15. A reprovacao do pre-commit se classifica por CAUSA, e as tres nao se confundem
# ---------------------------------------------------------------------------
# O caso que obriga isto foi medido nesta sessao, num commit do maestro que
# reprovou por CONTENCAO e passou na retentativa sem uma linha alterada. Se a
# cadeia lesse aquilo como recusa de conteudo, a peca ficaria parada para sempre
# por defeito que nao e' dela -- o "travar a toa" que o dono nomeou.
classe_de() {
	python3 - "$RAIZ/tools/cerebro-commitar" "$1" <<'PYCLASSE'
import importlib.machinery, importlib.util, sys
caminho, texto = sys.argv[1:3]
spec = importlib.util.spec_from_loader(
    "cc", importlib.machinery.SourceFileLoader("cc", caminho))
modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)
classe, codigo, _ = modulo.classifica(texto)
print(f"{classe} {codigo}")
PYCLASSE
}
confere "$(classe_de 'go-index-compile-closure: REPROVADO: compile closure excedeu 76.5s concedidos (teto de compilação 120s)
pre-commit: comando reprovou rc=1')" "ambiente 3" \
	"o caso REAL medido nesta sessao tem de ser AMBIENTE: ele passou na retentativa sem uma linha alterada"
confere "$(classe_de "fatal: Unable to create '/opt/wiki/.git/index.lock': File exists")" "ambiente 3" \
	"index.lock ocupado por outro processo e' contencao, nunca defeito da peca"
# ★ CADA PADRAO ISOLADO, e este bloco nasceu de dois mutantes que SOBREVIVERAM.
#
# Os dois casos acima casam DOIS padroes de ambiente cada um ("compile closure
# excedeu" e "teto de compilação"; "index.lock" e "Unable to create"). Remover um
# deles nao mudava a classe, e o mutante passava despercebido: a fixture media o
# conjunto, nao a regra. Aqui cada texto tem UM unico marcador.
confere "$(classe_de 'compile closure excedeu o concedido')" "ambiente 3" \
	"o padrao 'compile closure excedeu' tem de decidir SOZINHO"
confere "$(classe_de 'erro ao abrir .git/index.lock')" "ambiente 3" \
	"o padrao 'index.lock' tem de decidir SOZINHO"
confere "$(classe_de 'Resource temporarily unavailable')" "ambiente 3" \
	"indisponibilidade de recurso tem de decidir SOZINHA"
confere "$(classe_de 'ModuleNotFoundError: No module named z')" "hook 4" \
	"o padrao de hook tem de decidir SOZINHO"
confere "$(classe_de 'Traceback (most recent call last):
  File "tools/check-x", line 3, in <module>
ModuleNotFoundError: No module named y')" "hook 4" \
	"gate que estourou com Traceback e' defeito do HOOK: a peca retoma E o defeito vira alerta"
confere "$(classe_de 'pre-commit: produto rastreado sumiu da worktree sem cópia preservada ao lado.
pre-commit: comando reprovou rc=1')" "peca 1" \
	"defeito de conteudo tem de ser PECA: quarentena que espera correcao"
confere "$(classe_de 'check-v2-finalized-commit: REPROVADO: intent sem linha no portfolio do commit pai')" "peca 1" \
	"gate de conteudo e' PECA"
confere "$(classe_de 'algo que nenhum padrao conhece')" "peca 1" \
	"o DEFAULT tem de ser a classe conservadora: tratar o desconhecido como ambiente faria defeito real virar laco infinito"
# A ORDEM IMPORTA: hook ANTES de ambiente. Um gate que estourou com Traceback
# costuma imprimir 'timeout' na linha seguinte, e hook quebrado disfarcado de
# contencao nunca viraria alerta.
confere "$(classe_de 'Traceback (most recent call last): ...
timed out')" "hook 4" \
	"hook tem de vencer ambiente quando os dois padroes aparecem: senao gate quebrado nunca vira alerta"

if ((falhas > 0)); then
	printf 'test_publicador_do_cerebro: %s falha(s)\n' "$falhas" >&2
	exit 1
fi
echo "test_publicador_do_cerebro: ok"
