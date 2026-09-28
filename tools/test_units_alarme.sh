#!/usr/bin/env bash
# Prova que check-units-alarme REPROVA o caso ruim e ACEITA o legitimo.
#
# POR QUE ESTE TESTE EXISTE, e por que ele nasce junto com o gate: um detector
# que so foi visto passar no caso certo nao esta testado -- ja houve neste
# repositorio um detector que acusou 46 paginas sendo que as 46 eram falso
# positivo. Aqui a metade que importa e a de baixo: as units de SUPORTE, o
# proprio canal de alerta e a mascara JUSTIFICADA nao podem ser acusadas.
#
# A regressao nomeada (caso 2) e o erro que originou o gate: um levantamento
# contou "3 de 26 units com OnFailure" porque `grep -l` casou a palavra dentro
# de COMENTARIO. O numero real era 1. Uma unit cujo unico OnFailure esta
# comentado TEM de reprovar.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
# Sobrescrevivel para o teste de MUTACAO: um teste que nunca reprova nao prova
# nada, entao ele tem de ser rodavel contra uma copia quebrada do gate.
#   GATE_UNITS_ALARME=/tmp/gate-mutante ./tools/test_units_alarme.sh   -> REPROVADO
GATE=${GATE_UNITS_ALARME:-./tools/check-units-alarme}
falhou=0
passo() { printf '  %s %s\n' "$1" "$2"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Cria uma raiz de fixture com o canal de alerta ja presente (toda unit que
# aponta OnFailure para ele precisa que o arquivo exista - regra R-B).
novo_caso() {
	d="$TMP/$1"
	mkdir -p "$d/ops/systemd"
	cat >"$d/ops/systemd/wikijuridica-alerta@.service" <<'EOF'
[Unit]
Description=Alerta de falha da unit %i
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/notify-owner --chave "unit-falhou-%i" --titulo "Unit %i falhou"
EOF
	echo "$d"
}

# roda o gate na raiz $1; guarda saida em $SAIDA e codigo em $CODIGO
roda() {
	SAIDA=$(WIKI_ROOT="$1" $GATE 2>&1)
	CODIGO=$?
}

# espera reprovacao (exit 1) mencionando a regra $2 e a unit $3
espera_fail() {
	roda "$1"
	if [[ $CODIGO -eq 1 && "$SAIDA" == *"$2"* && "$SAIDA" == *"$3"* ]]; then
		passo OK "$4"
	else
		passo FALHA "$4 (exit=$CODIGO) :: $(echo "$SAIDA" | tail -3 | tr '\n' ' ')"
		falhou=1
	fi
}

espera_ok() {
	roda "$1"
	if [[ $CODIGO -eq 0 ]]; then
		passo OK "$2"
	else
		passo FALHA "$2 -- acusou indevidamente (exit=$CODIGO) :: $(echo "$SAIDA" | grep -A1 '^  - ' | head -4 | tr '\n' ' ')"
		falhou=1
	fi
}

echo "== O GATE TEM DE REPROVAR"

# ---------- caso 1: unit agendada sem OnFailure nenhum
d=$(novo_caso sem-onfailure)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia qualquer
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-A" "wikijuridica-vigia.service" "unit agendada sem OnFailure e acusada"

# ---------- caso 2: REGRESSAO NOMEADA -- OnFailure so no comentario
d=$(novo_caso onfailure-comentado)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com OnFailure so na prosa
# Esta unit MENCIONA OnFailure=wikijuridica-alerta@%N.service no comentario,
# exatamente como o cabecalho que fez o levantamento contar 3 em vez de 1.
#OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-A" "wikijuridica-vigia.service" "OnFailure comentado NAO conta como diretiva"

# ---------- caso 3: SuccessExitStatus sem comentario adjacente
d=$(novo_caso mascara-sem-razao)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia que mascara sem dizer porque
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
SuccessExitStatus=0 1
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-E" "SuccessExitStatus=0 1" "mascara sem razao registrada e acusada"

# ---------- caso 4: %n em vez de %N
d=$(novo_caso especificador-errado)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com o especificador que duplica o sufixo
OnFailure=wikijuridica-alerta@%n.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-C" "wikijuridica-vigia.service" "%n em vez de %N e acusado"

# ---------- caso 5: OnFailure apontando para unit que nao existe
d=$(novo_caso alvo-inventado)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia que inventou uma unit de alerta
OnFailure=wikijuridica-alarme-novo@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-B" "wikijuridica-alarme-novo" "alvo de OnFailure inexistente e acusado"

# ---------- caso 6: OnFailure na secao errada (o systemd IGNORA em silencio)
d=$(novo_caso secao-errada)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com OnFailure no lugar errado
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
OnFailure=wikijuridica-alerta@%N.service
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-D" "wikijuridica-vigia.service" "OnFailure em [Service] e acusado (systemd ignora ali)"

# ---------- caso 7: LACO -- o proprio canal de alerta com OnFailure
d=$(novo_caso laco-do-canal)
cat >"$d/ops/systemd/wikijuridica-alerta@.service" <<'EOF'
[Unit]
Description=Alerta de falha da unit %i
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/notify-owner --chave "unit-falhou-%i" --titulo "Unit %i falhou"
EOF
espera_fail "$d" "R-LACO" "wikijuridica-alerta@.service" "canal de alerta que se alerta e acusado"

# ---------- caso 8: timer SEM Unit= (mapeia pelo basename) tambem exige OnFailure
d=$(novo_caso timer-implicito)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia disparado por timer sem Unit=
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\n[Install]\nWantedBy=timers.target\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-A" "wikijuridica-vigia.service" "timer sem Unit= mapeia pelo basename e exige OnFailure"

# ---------- caso 9: justificativa trivial nao passa pelo piso de prosa
d=$(novo_caso razao-trivial)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com comentario decorativo
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
# SuccessExitStatus
SuccessExitStatus=0 1
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-E" "sem comentario adjacente" "comentario que so repete o nome da diretiva nao e razao"

echo
echo "== FALSOS POSITIVOS: O GATE NAO PODE ACUSAR"

# ---------- FALSO POSITIVO 1: unit de SUPORTE (oneshot sem timer, chamada por outra)
d=$(novo_caso fp-suporte)
cat >"$d/ops/systemd/wikijuridica-passo-interno.service" <<'EOF'
[Unit]
Description=passo chamado por outra unit, sem timer proprio
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/generate-alguma-coisa
EOF
espera_ok "$d" "unit de suporte sem timer NAO e acusada"

# ---------- FALSO POSITIVO 2: .timer nao e .service e nao se avalia
d=$(novo_caso fp-timer)
printf '[Unit]\nDescription=so um timer\n[Timer]\nOnCalendar=hourly\n[Install]\nWantedBy=timers.target\n' \
	>"$d/ops/systemd/wikijuridica-orfao.timer"
espera_ok "$d" "arquivo .timer NAO e acusado por falta de OnFailure"

# ---------- FALSO POSITIVO 3: mascara COM justificativa adjacente
d=$(novo_caso fp-mascara-justificada)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com mascara legitima
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
# Exit 1 e o veredito do vigia sobre o mundo medido, nao defeito do vigia: ele
# fica no journal e na serie JSONL. Marcar a unit como falha so produziria ruido.
SuccessExitStatus=0 1
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_ok "$d" "mascara com razao adjacente NAO e acusada"

# ---------- FALSO POSITIVO 4: o canal de alerta SEM OnFailure (tem de ficar assim)
d=$(novo_caso fp-canal-limpo)
espera_ok "$d" "canal de alerta sem OnFailure NAO e acusado (e o desenho correto)"

# ---------- FALSO POSITIVO 5: daemon com Restart= nao exige OnFailure
d=$(novo_caso fp-daemon)
cat >"$d/ops/systemd/wikijuridica-daemon.service" <<'EOF'
[Unit]
Description=daemon supervisionado
StartLimitIntervalSec=0
[Service]
Type=simple
ExecStart=/opt/wiki/bin/algum-daemon
Restart=always
RestartSec=5
EOF
espera_ok "$d" "daemon com Restart= NAO e acusado"

# ---------- FALSO POSITIVO 6: template (@) nao e acusado
d=$(novo_caso fp-template)
cat >"$d/ops/systemd/cloudflared-replica@.service" <<'EOF'
[Unit]
Description=replica %i
[Service]
Type=notify
ExecStart=/usr/bin/cloudflared tunnel run
EOF
espera_ok "$d" "unit template NAO e acusada"

echo
echo "== CONTRATO DE SAIDA"

# ---------- exit 2 (INCONCLUSIVO), nunca 1, quando nao da para medir
roda "$TMP/raiz-que-nao-existe"
if [[ $CODIGO -eq 2 ]]; then
	passo OK "raiz inexistente devolve 2 (inconclusivo), nao reprovacao"
else
	passo FALHA "raiz inexistente devolveu $CODIGO, deveria ser 2"
	falhou=1
fi

d="$TMP/vazio"
mkdir -p "$d/ops/systemd"
roda "$d"
if [[ $CODIGO -eq 2 ]]; then
	passo OK "diretorio sem unit devolve 2, nao um OK vazio"
else
	passo FALHA "diretorio vazio devolveu $CODIGO, deveria ser 2"
	falhou=1
fi

# ---------- --json e legivel por maquina e carrega o denominador
d=$(novo_caso json)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia sem aviso
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-alguma-coisa
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
saida_json=$(WIKI_ROOT="$d" $GATE --json)
codigo_json=$?
if echo "$saida_json" | python3 -m json.tool >/dev/null 2>&1; then
	passo OK "--json produz JSON valido"
else
	passo FALHA "--json nao e JSON valido"
	falhou=1
fi
if [[ $codigo_json -eq 1 ]]; then
	passo OK "--json preserva o exit 1 da reprovacao"
else
	passo FALHA "--json devolveu $codigo_json, deveria ser 1"
	falhou=1
fi
# Armadilha 3 deste repo: quem informa cobertura tem de informar o denominador.
if echo "$saida_json" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if 'units_service_total' in d and 'exigem_onfailure' in d else 1)"; then
	passo OK "--json traz o denominador ao lado da contagem"
else
	passo FALHA "--json sem denominador"
	falhou=1
fi

# ══════════════════════════════════════════════════════════════════════════
# R-F — ALARME INALCANCAVEL (acrescentado em 2026-09-16)
#
# A classe de defeito que nenhum grep encontra: a unit declara OnFailure, tem
# Restart=always, e o burst de reinicio NUNCA e atingido dentro da janela. Ela
# nao entra em `failed`, e o OnFailure e decoracao.
echo
echo "== R-F: O ALARME QUE NUNCA PODE DISPARAR"

# ---------- caso R-F.1: RestartSec x Burst nao cabe na janela, e NAO ha detector
# 15s x 5 = 75s de burst contra a janela default do manager (10s).
d=$(novo_caso alarme-inalcancavel)
cat >"$d/ops/systemd/wikijuridica-processador.service" <<'EOF'
[Unit]
Description=daemon que processa
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=simple
ExecStart=/opt/wiki/bin/processador
Restart=always
RestartSec=15
EOF
espera_fail "$d" "R-F" "wikijuridica-processador.service" \
	"Restart=always+RestartSec=15 sem StartLimit: OnFailure inalcancavel e acusado"

# ---------- caso R-F.2: A FIXTURE DA SECAO ERRADA.
# StartLimitIntervalSec=300 em [Service] "consertaria" a aritmetica SE valesse.
# Ela NAO vale: o systemd responde "Unknown key 'StartLimitIntervalSec' in
# section [Service], ignoring" (medido com systemd-analyze verify em
# 2026-09-16) e o default de 10s segue valendo. Um gate que lesse a diretiva
# SEM olhar a secao daria esta unit como corrigida — e ela continua muda.
# Este e o caso que o repositorio ja pagou uma vez
# (ops/systemd/wikijuridica-social.service:84: "so `systemctl show` revelou").
d=$(novo_caso startlimit-na-secao-errada)
cat >"$d/ops/systemd/wikijuridica-processador.service" <<'EOF'
[Unit]
Description=daemon com StartLimitIntervalSec na secao errada
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=simple
ExecStart=/opt/wiki/bin/processador
Restart=always
RestartSec=15
StartLimitIntervalSec=300
EOF
espera_fail "$d" "R-F" "wikijuridica-processador.service" \
	"StartLimitIntervalSec em [Service] NAO conserta o alarme (o systemd a ignora)"
# E a mensagem tem de NOMEAR a secao, senao quem ler nao sabe o que mover.
if [[ "$SAIDA" == *"[Service]"* && "$SAIDA" == *"[Unit]"* ]]; then
	passo OK "a mensagem diz de qual secao para qual secao mover"
else
	passo FALHA "R-F nao explica a secao :: $(echo "$SAIDA" | grep -A1 R-F | head -2 | tr '\n' ' ')"
	falhou=1
fi

# ---------- caso R-F.3: a MESMA unit com a diretiva na secao CERTA passa.
# Sem este par, o caso acima provaria apenas "o gate reclama de StartLimit", e
# nao "o gate le a secao".
d=$(novo_caso startlimit-na-secao-certa)
cat >"$d/ops/systemd/wikijuridica-processador.service" <<'EOF'
[Unit]
Description=daemon com StartLimitIntervalSec no lugar certo
OnFailure=wikijuridica-alerta@%N.service
StartLimitIntervalSec=300
[Service]
Type=simple
ExecStart=/opt/wiki/bin/processador
Restart=always
RestartSec=15
EOF
espera_ok "$d" "StartLimitIntervalSec=300 em [Unit] torna o alarme alcancavel e PASSA"

# ---------- caso R-F.4: detector declarado que NAO EXISTE no disco
d=$(novo_caso detector-fantasma)
cat >"$d/ops/systemd/wikijuridica-cerebro.service" <<'EOF'
[Unit]
Description=cerebro
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=simple
ExecStart=/opt/wiki/bin/cerebro
Restart=always
RestartSec=15
EOF
# A allowlist aponta para tools/check-cerebro-vivo, e nesta raiz de fixture ele
# nao existe: detector declarado e ausente e pior que detector nenhum, porque
# parece cobertura.
espera_fail "$d" "R-F" "wikijuridica-cerebro.service" \
	"detector nomeado ausente do disco e acusado (cobertura so no papel)"

# ══════════════════════════════════════════════════════════════════════════
# R-G — O QUE PODE SER MASCARADO
echo
echo "== R-G: MASCARA COM LIMITE"

# ---------- caso R-G.1: mascarar o 2 reprova SEMPRE.
# 2 significa "NAO MEDI", e nao medir nunca e sucesso. Esta e a unica regra
# desta familia que nao tem excecao.
d=$(novo_caso mascara-o-dois)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia que mascara o codigo de nao-medicao
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-units-alarme
# Justificativa longa o bastante para satisfazer R-E, de proposito: o que
# reprova aqui NAO e a falta de prosa, e o codigo escolhido.
SuccessExitStatus=0 1 2
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_fail "$d" "R-G" "wikijuridica-vigia.service" \
	"mascarar o exit 2 (NAO MEDI) e acusado mesmo com justificativa escrita"

# ---------- caso R-G.2: mascarar 1 e 75 e legitimo.
d=$(novo_caso mascara-legitima)
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<'EOF'
[Unit]
Description=vigia com mascara legitima
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=/opt/wiki/tools/check-units-alarme
# Exit 1 e VEREDITO MEDIDO (o gate reprovou o que mediu) e 75 e EX_TEMPFAIL
# (falha temporaria); alertar em qualquer um dos dois vira ruido de rotina.
SuccessExitStatus=0 1 75
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
espera_ok "$d" "mascarar 1 e 75 com razao registrada PASSA"

# ---------- caso R-G.3: mascara exit 1 chamando ferramenta SEM protecao crash->2.
# O defeito estrutural de 2026-09-16: traceback -> exit 1 -> mascarado ->
# Result=success -> OnFailure mudo.
d=$(novo_caso mascara-sem-protecao)
mkdir -p "$d/tools"
cat >"$d/tools/check-desprotegido" <<'EOF'
#!/usr/bin/env python3
import sys
def main():
    return 1
if __name__ == "__main__":
    sys.exit(main())
EOF
chmod +x "$d/tools/check-desprotegido"
cat >"$d/ops/systemd/wikijuridica-vigia.service" <<EOF
[Unit]
Description=vigia que mascara 1 sobre ferramenta desprotegida
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
ExecStart=$d/tools/check-desprotegido
# Exit 1 e veredito medido desta sonda, e alertar nele seria ruido diario.
SuccessExitStatus=0 1
EOF
printf '[Timer]\nOnCalendar=hourly\nUnit=wikijuridica-vigia.service\n' >"$d/ops/systemd/wikijuridica-vigia.timer"
WIKI_ROOT="$d" SAIDA=$(WIKI_ROOT="$d" $GATE 2>&1); CODIGO=$?
if [[ $CODIGO -eq 1 && "$SAIDA" == *"R-G"* && "$SAIDA" == *"check-desprotegido"* ]]; then
	passo OK "mascara de exit 1 sobre ferramenta sem crash->2 e acusada"
else
	passo FALHA "deveria acusar a ferramenta desprotegida (exit=$CODIGO) :: $(echo "$SAIDA" | tail -3 | tr '\n' ' ')"
	falhou=1
fi

# ---------- caso R-G.4: a MESMA unit, com a ferramenta protegida, passa.
# O par que impede a regra de virar "reprova sempre que houver ExecStart".
cat >"$d/tools/check-desprotegido" <<'EOF'
#!/usr/bin/env python3
import os
import sys
def main():
    return 1
if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
    from saida_de_medidor import main_protegido
    main_protegido(main)
EOF
espera_ok "$d" "a mesma unit PASSA quando a ferramenta usa main_protegido"

# ---------- caso R-H.1: PrivateTmp + caminho de /tmp na PROPRIA unit, sem bind.
# O flock escrito no ExecStart: dentro do /tmp privado ele tranca outro arquivo.
d=$(novo_caso privatetmp-flock-sem-bind)
cat >"$d/ops/systemd/wikijuridica-bancada.service" <<'EOF'
[Unit]
Description=bancada que serializa com flock dentro de PrivateTmp
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
PrivateTmp=true
ExecStart=/usr/bin/flock /tmp/opt-wiki-agent-heavy.lock /opt/wiki/tools/run-qualidade-diaria
EOF
printf '[Timer]\nOnCalendar=daily\nUnit=wikijuridica-bancada.service\n' >"$d/ops/systemd/wikijuridica-bancada.timer"
espera_fail "$d" "R-H" "wikijuridica-bancada.service" "flock de /tmp sob PrivateTmp sem BindPaths e acusado"

# ---------- caso R-H.2: a MESMA unit COM o bind passa.
# O par que impede a regra de virar "reprova toda unit com PrivateTmp".
cat >"$d/ops/systemd/wikijuridica-bancada.service" <<'EOF'
[Unit]
Description=bancada que serializa com flock dentro de PrivateTmp
OnFailure=wikijuridica-alerta@%N.service
[Service]
Type=oneshot
PrivateTmp=true
BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock
ExecStart=/usr/bin/flock /tmp/opt-wiki-agent-heavy.lock /opt/wiki/tools/run-qualidade-diaria
EOF
espera_ok "$d" "a mesma unit PASSA quando declara BindReadOnlyPaths para o lock"

# ---------- caso R-H.3: lock que mora no BINARIO (LOCKS_FORA_DA_UNIT).
# E o defeito real do cerebro: a unit nao menciona /tmp em lugar nenhum, o
# caminho esta no codigo Go, e quem der grep na unit nao acha nada.
d=$(novo_caso lock-no-binario-sem-bind)
mkdir -p "$d/internal/cerebro" "$d/cmd/cerebro" "$d/ops/tmpfiles.d"
printf 'package cerebro\n\nconst LockPesadoPadrao = "/tmp/opt-wiki-agent-heavy.lock"\n' \
	>"$d/internal/cerebro/saude.go"
cat >"$d/ops/systemd/wikijuridica-cerebro.service" <<'EOF'
[Unit]
Description=cerebro sem o bind do lock
[Service]
Type=simple
PrivateTmp=true
Restart=always
RestartSec=15
ExecStart=/opt/wiki/bin/cerebro servir
EOF
espera_fail "$d" "R-H" "wikijuridica-cerebro.service" "lock que mora no binario, sem bind, e acusado"

# ---------- caso R-H.4: com o bind, mas SEM o snippet tmpfiles.
# A terceira perna: /tmp e esvaziado no boot, e bind com `-` sobre origem
# ausente e pulado em silencio -- a mentira volta sem nada no disco para
# denuncia-la.
cat >"$d/ops/systemd/wikijuridica-cerebro.service" <<'EOF'
[Unit]
Description=cerebro com bind e sem tmpfiles
[Service]
Type=simple
PrivateTmp=true
Restart=always
RestartSec=15
BindReadOnlyPaths=-/tmp/opt-wiki-agent-heavy.lock
ExecStart=/opt/wiki/bin/cerebro servir
EOF
espera_fail "$d" "R-H" "tmpfiles" "bind sem snippet tmpfiles que crie o lock no boot e acusado"

# ---------- caso R-H.5: as tres pernas presentes -> passa.
printf 'f /tmp/opt-wiki-agent-heavy.lock 0644 rafael rafael -\n' \
	>"$d/ops/tmpfiles.d/wikijuridica-lock.conf"
espera_ok "$d" "bind + snippet tmpfiles + literal no codigo Go: as tres pernas passam"

# ---------- caso R-H.6: comentario NAO cria arquivo.
# Mesmo erro do `grep -l OnFailure` que originou este gate: o caminho citado
# dentro de um comentario do snippet nao cria coisa nenhuma.
cat >"$d/ops/tmpfiles.d/wikijuridica-lock.conf" <<'EOF'
# f /tmp/opt-wiki-agent-heavy.lock 0644 rafael rafael -
EOF
espera_fail "$d" "R-H" "tmpfiles" "caminho so no COMENTARIO do snippet nao conta como criado"

# ---------- a arvore REAL passa (o gate nasce verde porque as units foram corrigidas)
roda "$(pwd)"
if [[ $CODIGO -eq 0 ]]; then
	passo OK "ops/systemd real do repositorio passa"
else
	passo FALHA "a arvore real REPROVOU: $(echo "$SAIDA" | grep -A1 '^  - ' | head -6 | tr '\n' ' ')"
	falhou=1
fi

echo
if [[ $falhou -eq 0 ]]; then echo "check-units-alarme: sem defeito"; else echo "REPROVADO"; fi
exit $falhou
