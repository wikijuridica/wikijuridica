#!/usr/bin/env bash
# Bancada da TROCA DE BINARIO do `tools/deploy-publico`.
#
# ★ O DEPLOY QUE MORREU EM 2026-09-16
#
# O passo 5/7 falhou com `cp: nao foi possivel criar arquivo comum
# 'bin/wikijuridica-server': Area de texto ocupada` — ETXTBSY — DEPOIS de o
# passo 1/7 ja ter republicado o acervo. O acervo ficou no disco e o binario
# novo nao subiu.
#
# A causa nao e corrida rara: `cp` abre o DESTINO para escrita e escreve no
# lugar. O passo 3/7 para o servico, o passo 4/7 limpa 41 MB de cache do Go e
# 22.691 objetos do nginx — e nessa janela a unit, ATIVADA POR SOCKET, volta
# sozinha na primeira requisicao que chega. No passo 5/7 o binario ja esta em
# execucao outra vez.
#
# `mv` no mesmo sistema de arquivos e `rename(2)`: troca a entrada de diretorio
# e nao toca no inode antigo. Quem ja esta executando segue com o inode velho
# ate o restart — que e o passo seguinte — e a troca nunca da ETXTBSY.
#
# Esta bancada prova o COMPORTAMENTO, com um binario de verdade em execucao, e
# depois prova que o deploy usa a forma certa. As duas metades importam: a
# primeira explica POR QUE, a segunda garante que ninguem volte atras.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
falhas=0

reprova() {
	printf 'FALHA: %s\n' "$1" >&2
	falhas=$((falhas + 1))
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# --- Um BINARIO ELF de verdade, em execucao ----------------------------------
#
# ★ A PRIMEIRA VERSAO DESTA BANCADA USAVA UM SCRIPT, E O CONTROLE POSITIVO
#   FALHOU — corretamente.
#
# ETXTBSY vale para o arquivo que o kernel mantem mapeado como imagem de
# execucao: um ELF rodando. Script com `#!` e LIDO pelo interpretador, que o
# fecha; `cp` por cima funciona. Reproduzir o incidente com script teria dado
# uma bancada verde sobre um cenario que nao e o do defeito — verde por
# vacuidade, que e pior que vermelho.
#
# `/bin/sleep` e um ELF do sistema e serve de cobaia sem depender de compilar
# nada aqui.
cp /bin/sleep "$tmp/alvo"
cp /bin/true "$tmp/alvo.next"

"$tmp/alvo" 30 &
pid=$!
trap 'kill "$pid" 2>/dev/null; rm -rf "$tmp"' EXIT
# Espera o exec acontecer de fato: sem isto o teste correria antes de o arquivo
# ficar ocupado e passaria por vacuidade.
for _ in $(seq 1 100); do
	if [ "$(readlink -f "/proc/$pid/exe" 2>/dev/null)" = "$(readlink -f "$tmp/alvo")" ]; then break; fi
	timeout 0.1 tail -f /dev/null 2>/dev/null || true
done

# --- CONTROLE POSITIVO: `cp` sobre binario em execucao FALHA -----------------
# Sem este caso, a bancada nao prova que o defeito existe — e regra que nunca
# viu o defeito e regra nao provada.
if cp "$tmp/alvo.next" "$tmp/alvo" 2>/dev/null; then
	reprova "cp sobre binario em execucao NAO falhou neste kernel — o cenario do incidente nao foi reproduzido, e o resto desta bancada nao prova nada"
fi

# --- O QUE IMPORTA: `mv` sobre binario em execucao FUNCIONA ------------------
if ! mv "$tmp/alvo.next" "$tmp/alvo" 2>/dev/null; then
	reprova "mv sobre binario em execucao falhou: a correcao do deploy nao resolve"
fi
if ! cmp -s "$tmp/alvo" /bin/true; then
	reprova "depois do mv o arquivo nao tem o conteudo NOVO"
fi
# E o processo que ja rodava continua vivo, com o inode velho.
if ! kill -0 "$pid" 2>/dev/null; then
	reprova "o processo em execucao morreu com o mv: rename nao pode derrubar quem ja roda"
fi

# --- O PONTO DE CHAMADA, e nao so o comportamento ---------------------------
# A funcao pode estar certa e o deploy continuar usando cp. Foi assim que dois
# mutantes sobreviveram a outras bancadas nesta mesma sessao.
if grep -qE '^\s*cp bin/wikijuridica-server\.next bin/wikijuridica-server' "$RAIZ/tools/deploy-publico"; then
	reprova "o deploy voltou a trocar o binario do servidor com cp — ETXTBSY garantido sob socket ativo"
fi
if ! grep -qE '^\s*mv bin/wikijuridica-server\.next bin/wikijuridica-server' "$RAIZ/tools/deploy-publico"; then
	reprova "o deploy nao troca o binario do servidor com mv"
fi
# A irmã que sempre esteve certa continua certa.
if ! grep -qE '^\s*mv bin/wikijuridica-social\.next bin/wikijuridica-social' "$RAIZ/tools/deploy-publico"; then
	reprova "a troca do binario da rede social deixou de usar mv"
fi
# E o backup continua por cp, que ali esta CERTO: o binario velho e a ORIGEM.
if ! grep -qE '^\s*cp bin/wikijuridica-server bin/wikijuridica-server\.anterior' "$RAIZ/tools/deploy-publico"; then
	reprova "o backup do binario anterior sumiu: sem ele nao ha para onde voltar"
fi

if ((falhas > 0)); then
	printf 'test_troca_de_binario: %s falha(s)\n' "$falhas" >&2
	exit 1
fi
echo "test_troca_de_binario: ok"
