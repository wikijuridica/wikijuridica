#!/usr/bin/env bash
# Prova, por MUTAÇÃO, que o reparo do vigia CURA a unit ausente em vez de repetir
# `systemctl restart` — e que a cura deixa a unit `enabled`, não `linked`.
#
# O CASO REPRODUZIDO é o de 01–02/09/2026, na forma exata do journal:
#
#     set 01 18:37:00 wikijuridica-server.service: Main process exited, status=1
#     set 01 18:37:05 wikijuridica-server.service: Failed to schedule restart job:
#                     Unit wikijuridica-server.socket not found
#
# O `.service` exigia um `.socket` que o systemd não tinha. `Restart=always`
# ficou inerte, o serviço passou 16 h em `failed` e o vigia repetiu 493 restarts
# fúteis com a mesma mensagem.
#
# TRÊS VERSÕES DO VIGIA CORREM O MESMO CASO, e é a diferença entre elas que é a
# prova — teste que só vê o verde não prova nada:
#   antes  (4350a318^) só reinicia            -> tem de registrar restart_falhou
#   HEAD   (4350a318)  faz `ln -sf`           -> cura o boot de HOJE e deixa a
#                                                unit `linked`: some no reboot
#   hoje   (worktree)  faz `systemctl enable` -> deixa `enabled`, e reinicia UMA vez
#
# COMO O TESTE NÃO TOCA NO HOST. Três isolamentos, nenhum opcional:
#   1. o vigia roda de uma CÓPIA num diretório temporário. `ROOT` é derivado do
#      caminho do script, então ESTADO, HISTORICO, DIR_UNITS_REPO, BINARIO,
#      NOTIFICADOR e o lock de deploy passam todos a apontar para lá;
#   2. as duas URLs de sonda (`GO`/`NGINX`) são reescritas para uma porta fechada
#      — é a ÚNICA edição feita na cópia, e o teste a confere abaixo, para que
#      ninguém possa dizer que provou outro código;
#   3. `sudo`, `systemctl` e `ln` são substituídos por shims no PATH que GRAVAM
#      cada argv e devolvem a saída literal do systemd. Os shims têm ESTADO: a
#      unit mutada nasce `not-found`; `ln` a torna `linked`; `enable` a torna
#      `enabled`. Sem esse estado o teste não distinguiria cura de ruído, nem
#      `linked` de `enabled` — que é a diferença que ele existe para medir.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RAIZ=$PWD
T=$(mktemp -d "${TMPDIR:-/tmp}/portal-health-mutacao.XXXXXX")
trap 'rm -rf "$T"' EXIT
falhou=0

ok() { echo "  ok   — $1"; }
erro() {
	echo "  ERRO — $1"
	falhou=1
}

# ── shims ────────────────────────────────────────────────────────────────────
mkdir -p "$T/bin"
cat >"$T/bin/systemctl" <<'SHIM'
#!/usr/bin/env bash
# Grava argv em $SHIM_LOG e devolve saída literal do systemd.
# $SHIM_LOAD  = LoadState da unit mutada   (not-found | loaded)
# $SHIM_ENAB  = is-enabled da unit mutada  (not-found | linked | enabled)
echo "systemctl $*" >> "$SHIM_LOG"
args=("$@")
case "${args[0]}" in
  show)
    unit=${args[1]}; prop=""
    for i in "${!args[@]}"; do [[ ${args[$i]} == "-p" ]] && prop=${args[$((i+1))]}; done
    case "$prop" in
      "Requires,Wants")
        # Saída literal do host, medida em 2026-09-05 com
        #   systemctl show wikijuridica-server -p Requires,Wants
        # e com o nome do socket trocado pelo mutado.
        echo "Requires=wikijuridica-server-mutado.socket system.slice sysinit.target"
        echo "Wants=network-online.target"
        ;;
      LoadState)
        if [[ $unit == *wikijuridica-server-mutado.socket ]]; then cat "$SHIM_LOAD"; else echo loaded; fi ;;
      ActiveState) echo failed ;;
      NRestarts)   echo 0 ;;
      *)           echo "" ;;
    esac
    ;;
  is-enabled)
    unit=${args[*]}
    if [[ $unit == *wikijuridica-server-mutado.socket* ]]; then
      palavra=$(cat "$SHIM_ENAB"); echo "$palavra"
      [[ $palavra == enabled ]] || exit 1
    else
      echo enabled
    fi
    ;;
  enable)
    for a in "${args[@]}"; do
      if [[ $a == *wikijuridica-server-mutado.socket ]]; then
        echo loaded > "$SHIM_LOAD"; echo enabled > "$SHIM_ENAB"
        /bin/ln -sf "$a" "$SHIM_ETC/"; mkdir -p "$SHIM_ETC/sockets.target.wants"
        /bin/ln -sf "$a" "$SHIM_ETC/sockets.target.wants/"
      fi
    done
    ;;
  daemon-reload) : ;;
  restart)
    if [[ $(cat "$SHIM_LOAD") == not-found ]]; then
      echo "Failed to restart wikijuridica-server.service: Unit wikijuridica-server-mutado.socket not found." >&2
      exit 1
    fi
    ;;
  *) : ;;
esac
exit 0
SHIM
cat >"$T/bin/sudo" <<'SHIM'
#!/usr/bin/env bash
while [[ ${1:-} == -n ]]; do shift; done
exec "$@"
SHIM
cat >"$T/bin/ln" <<'SHIM'
#!/usr/bin/env bash
# `ln -sf <origem> /etc/systemd/system/` do vigia antigo, desviado para o
# sandbox: torna a unit `linked` — conhecida pelo systemd, ausente do boot.
echo "ln $*" >> "$SHIM_LOG"
# `ln -sf SRC DEST`: a ORIGEM e o primeiro argumento que nao e flag. Pegar o
# ultimo caminho existente pegaria o DESTINO (o diretorio), que existe sempre.
origem=""
for a in "$@"; do
  [[ $a == -* ]] && continue
  origem=$a; break
done
if [[ $origem == *wikijuridica-server-mutado.socket ]]; then
  echo loaded > "$SHIM_LOAD"; echo linked > "$SHIM_ENAB"
  /bin/ln -sf "$origem" "$SHIM_ETC/"
fi
exit 0
SHIM
chmod +x "$T/bin/systemctl" "$T/bin/sudo" "$T/bin/ln"

# ── monta uma cópia do vigia com a ÚNICA edição declarada ────────────────────
monta() { # $1 = destino  $2 = fonte do vigia
	rm -rf "$1"
	mkdir -p "$1/tools" "$1/ops/systemd" "$1/data/ops" "$1/bin"
	sed -e 's|^GO = .*|GO = "http://127.0.0.1:1"|' \
		-e 's|^NGINX = .*|NGINX = "http://127.0.0.1:1"|' "$2" >"$1/tools/check-portal-health"
	chmod +x "$1/tools/check-portal-health"
	sed 's/^Requires=wikijuridica-server\.socket$/Requires=wikijuridica-server-mutado.socket/' \
		"$RAIZ/ops/systemd/wikijuridica-server.service" >"$1/ops/systemd/wikijuridica-server.service"
	cp "$RAIZ/ops/systemd/wikijuridica-server.socket" "$1/ops/systemd/wikijuridica-server-mutado.socket"
	# Binário que herda o socket e fala notify: sem isso o vigia cairia no ramo
	# `binario_desatualizado` e o teste nunca exercitaria o reparo de unit.
	printf 'LISTEN_FDS NOTIFY_SOCKET' >"$1/bin/wikijuridica-server"
}

roda() { # $1 = diretório montado
	export SHIM_LOG="$1/shim.log" SHIM_LOAD="$1/loadstate" SHIM_ENAB="$1/isenabled" SHIM_ETC="$1/etc"
	mkdir -p "$SHIM_ETC"
	: >"$SHIM_LOG"
	echo not-found >"$SHIM_LOAD"
	echo not-found >"$SHIM_ENAB"
	PATH="$T/bin:$PATH" "$1/tools/check-portal-health" --repair >"$1/saida.txt" 2>&1
}

# ── o vigia de HOJE ──────────────────────────────────────────────────────────
monta "$T/hoje" "$RAIZ/tools/check-portal-health"
divergentes=$(diff "$RAIZ/tools/check-portal-health" "$T/hoje/tools/check-portal-health" | grep -c '^[<>]')
[[ $divergentes -eq 4 ]] &&
	ok "a cópia sob teste difere do vigia real em 2 linhas (as duas URLs de sonda)" ||
	erro "a cópia divergiu em $((divergentes / 2)) linha(s), esperado 2 — não prova o código real"

roda "$T/hoje"
log=$T/hoje/shim.log
grep -q "systemctl enable -- $T/hoje/ops/systemd/wikijuridica-server-mutado.socket" "$log" &&
	ok "hoje: habilitou a unit ausente (systemctl enable com o caminho do repositório)" ||
	erro "hoje: NÃO habilitou a unit ausente; shim.log: $(tr '\n' '|' <"$log")"
grep -q "systemctl daemon-reload" "$log" &&
	ok "hoje: recarregou o systemd depois de habilitar" ||
	erro "hoje: não recarregou o systemd"
n_enable=$(grep -n 'systemctl enable' "$log" | head -1 | cut -d: -f1)
n_restart=$(grep -n 'systemctl restart' "$log" | head -1 | cut -d: -f1)
if [[ -n $n_enable && -n $n_restart && $n_enable -lt $n_restart ]]; then
	ok "hoje: curou ANTES de reiniciar (enable na linha $n_enable, restart na $n_restart)"
else
	erro "hoje: ordem errada — enable=${n_enable:-nenhum} restart=${n_restart:-nenhum}"
fi
[[ $(grep -c 'systemctl restart' "$log") -eq 1 ]] &&
	ok "hoje: reiniciou UMA vez, com sucesso (não repetiu o fútil)" ||
	erro "hoje: restarts no log = $(grep -c 'systemctl restart' "$log")"
grep -q 'dependencia_instalada:wikijuridica-server-mutado.socket' "$T/hoje/saida.txt" &&
	ok "hoje: a saída declara a dependência instalada" ||
	erro "hoje: a saída não declara a instalação — $(tail -2 "$T/hoje/saida.txt" | tr '\n' '|')"
grep -q 'restart_falhou' "$T/hoje/saida.txt" &&
	erro "hoje: ainda registra restart_falhou" ||
	ok "hoje: nenhum restart_falhou na saída"
[[ $(cat "$T/hoje/isenabled") == enabled ]] &&
	ok "hoje: a unit terminou \`enabled\` — sobrevive ao reboot" ||
	erro "hoje: a unit terminou \`$(cat "$T/hoje/isenabled")\`, não \`enabled\`"
[[ -L "$T/hoje/etc/sockets.target.wants/wikijuridica-server-mutado.socket" ]] &&
	ok "hoje: o symlink que o BOOT lê foi criado" ||
	erro "hoje: nenhum symlink em sockets.target.wants"

# ── MUTAÇÃO 1: o vigia que instalava com `ln -sf`, sem habilitar ─────────────
#
# ★ A ÂNCORA É UM COMMIT FIXO, NUNCA `HEAD` (corrigido em 2026-09-05).
#
# Esta mutação nasceu apontando para `HEAD:tools/check-portal-health`, quando o
# conserto ainda estava só na árvore de trabalho. No instante em que ele foi
# commitado, `HEAD` passou a ser o vigia CORRIGIDO e a mutação virou inválida
# sozinha — o teste passou a reprovar com "mutação 1 inválida: o vigia de HEAD
# já habilitava", sem que nada no produto tivesse quebrado. Ficou vermelho no
# ledger diário assim.
#
# Prova por mutação precisa de alvo IMUTÁVEL: `a218b1de` é o commit que trocou
# o `ln -sf` por `systemctl enable`, então `a218b1de^` é, para sempre, a versão
# que instalava sem habilitar. É a mesma forma que a mutação 2 já usava
# (`4350a318^`) e que não expirou.
#
# O aviso "mutação inválida" continua sendo o comportamento certo: ele é a
# guarda que denuncia âncora podre. Foi ele que apontou este defeito.
MUTACAO_1_ANCORA='a218b1de^:tools/check-portal-health'
if git -C "$RAIZ" show "$MUTACAO_1_ANCORA" >"$T/vigia-head" 2>/dev/null; then
	monta "$T/head" "$T/vigia-head"
	roda "$T/head"
	grep -q 'systemctl enable' "$T/head/shim.log" &&
		erro "mutação 1 inválida: $MUTACAO_1_ANCORA já habilitava" ||
		ok "mutação 1: o vigia de $MUTACAO_1_ANCORA instala com \`ln\`, sem habilitar"
	[[ $(cat "$T/head/isenabled") == linked ]] &&
		ok "mutação 1: e por isso a unit fica \`linked\` — o portal volta hoje e some no reboot" ||
		erro "mutação 1: esperava \`linked\`, veio \`$(cat "$T/head/isenabled")\`"
else
	erro "não consegui ler $MUTACAO_1_ANCORA"
fi

# ── MUTAÇÃO 2: o vigia anterior ao conserto, que só reiniciava ───────────────
if git -C "$RAIZ" show '4350a318^:tools/check-portal-health' >"$T/vigia-antes" 2>/dev/null; then
	monta "$T/antes" "$T/vigia-antes"
	roda "$T/antes"
	grep -qE 'systemctl enable|^ln ' "$T/antes/shim.log" &&
		erro "mutação 2 inválida: o vigia de antes de 4350a318 já instalava algo" ||
		ok "mutação 2: o vigia de antes de 4350a318 não instala nada"
	grep -q 'restart_falhou' "$T/antes/saida.txt" &&
		ok "mutação 2: ele repete o restart fútil e registra restart_falhou" ||
		erro "mutação 2: esperava restart_falhou — $(tail -2 "$T/antes/saida.txt" | tr '\n' '|')"
else
	erro "não consegui ler 4350a318^:tools/check-portal-health — sem controle, não há prova"
fi

[[ $falhou -eq 0 ]] && echo "test_portal_health_reparo_unit_ausente: OK" ||
	echo "test_portal_health_reparo_unit_ausente: FAIL"
exit $falhou
