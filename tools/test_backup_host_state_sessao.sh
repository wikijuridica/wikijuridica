#!/usr/bin/env bash
# Prova a cobertura NOVA de tools/backup-host-state: a configuracao da sessao
# grafica (painel, lancadores, autostart) e a guarda de suspensao com o nome
# vivo do arquivo.
#
# POR QUE EXISTE. Ate 2026-09-10 o backup do host nao capturava NADA de
# ~/.config: xfce4-panel.xml, os rc dos plugins e os 12 lancadores do painel so
# existiam no HOME. Reinstalar o host perdia o painel inteiro. E a copia da
# guarda anti-suspensao apontava para `10-tampa-nao-suspende.conf`, nome que o
# host nao usa mais -- a copia versionada ficou congelada SEM HandleSuspendKey,
# HandleHibernateKey e IdleAction. Backup de guarda pela metade e pior que
# nenhum: restaurar aquela copia devolveria um host que aceita suspender.
#
# Este teste NAO roda o backup (que precisa de sudo e escreve no repo): ele le o
# codigo-fonte que vai para producao e confere o disco de host-state.
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
FONTE="$RAIZ/tools/backup-host-state"
ESTADO="$RAIZ/ops/host-state"
FALHAS=0
falhou() {
	printf 'FALHOU: %s\n' "$1" >&2
	FALHAS=$((FALHAS + 1))
}

# (a) o nome VIVO da guarda de suspensao esta na lista de copia
grep -q '/etc/systemd/logind.conf.d/no-suspend.conf' "$FONTE" ||
	falhou "no-suspend.conf (nome vivo da guarda) nao esta na lista de copia"

# (b) e a copia no disco tem as tres diretivas que faltavam na versao congelada
for d in HandleLidSwitch HandleSuspendKey HandleHibernateKey IdleAction; do
	grep -q "^$d=ignore" "$ESTADO/etc/no-suspend.conf" 2>/dev/null ||
		falhou "$ESTADO/etc/no-suspend.conf sem $d=ignore"
done

# (c) a copia versionada e IDENTICA ao que o host usa agora
if [ -r /etc/systemd/logind.conf.d/no-suspend.conf ]; then
	diff -q /etc/systemd/logind.conf.d/no-suspend.conf "$ESTADO/etc/no-suspend.conf" >/dev/null 2>&1 ||
		falhou "a copia de no-suspend.conf divergiu do arquivo do host"
fi

# (d) a secao da sessao grafica cobre os cinco alvos
for alvo in 'xfce4-panel.xml' 'xfce4-power-manager.xml' 'autostart/vigilia.desktop' \
	'vigilia-apagar-tela.desktop' 'panel/launcher-'; do
	grep -q "$alvo" "$FONTE" || falhou "backup-host-state nao cobre $alvo"
done

# (e) os globs de painel toleram diretorio vazio: sem `[ -e ]` o `set -e` deste
#     script mataria o backup do host quando nao houvesse nenhum .rc
grep -A2 'panel/\*\.rc' "$FONTE" | grep -q '\[ -e "\$f" \] || continue' ||
	falhou "o glob de *.rc nao protege contra diretorio vazio"

# (f) o fallback de plugin-ids procura panel-1 POR NOME. O primeiro `plugin-ids`
#     do XML e o do painel oculto `panel-99`: pegar o primeiro devolvia "204".
grep -q 'panel-1' "$FONTE" || falhou "o fallback de plugin-ids nao procura panel-1 por nome"
if command -v python3 >/dev/null 2>&1 && [ -r "$ESTADO/user/xfce4-panel.xml" ]; then
	ids=$(python3 -c '
import sys, xml.etree.ElementTree as ET
t = ET.parse(sys.argv[1])
for p in t.getroot().iter("property"):
    if p.get("name") == "panel-1":
        for c in p:
            if c.get("name") == "plugin-ids":
                print(" ".join(v.get("value") for v in c)); raise SystemExit(0)
' "$ESTADO/user/xfce4-panel.xml" 2>/dev/null)
	case " $ids " in
	*" 21 "*) : ;;
	*) falhou "o painel versionado nao tem o plugin 21 (genmon da vigilia): ids='$ids'" ;;
	esac
	case " $ids " in
	*" 22 "*) : ;;
	*) falhou "o painel versionado nao tem o plugin 22 (lancador de apagar a tela): ids='$ids'" ;;
	esac
	[ "$ids" = "204" ] && falhou "o fallback pegou o painel-99 em vez do painel-1"
fi

# (g) os dois arquivos do botao existem no host-state
for f in "$ESTADO/user/panel/genmon-21.rc" \
	"$ESTADO/user/panel/launcher-22-vigilia-apagar-tela.desktop" \
	"$ESTADO/user/vigilia.desktop"; do
	[ -s "$f" ] || falhou "faltando no host-state: $f"
done

# (h) o rc do genmon versionado NAO pode ter Font=(default): esse valor quebra o
#     CSS do plugin e o rotulo renderiza com largura zero (botao invisivel).
if [ -r "$ESTADO/user/panel/genmon-21.rc" ]; then
	grep -q 'Font=(default)' "$ESTADO/user/panel/genmon-21.rc" &&
		falhou "genmon-21.rc versionado tem Font=(default) — restaurar isso deixa o botao invisivel"
	grep -q 'Command=/opt/wiki/tools/vigilia genmon' "$ESTADO/user/panel/genmon-21.rc" ||
		falhou "genmon-21.rc versionado nao chama tools/vigilia genmon"
fi

# (i) rc ORFAO nao entra: o painel deixa `<tipo>-<id>.rc` para tras quando um
#     plugin e criado e descartado (2026-09-10: `genmon-8.rc` com Command vazio
#     de um `--add=genmon` que nao pegou, e `battery-18.rc` de uma renumeracao).
#     Um `genmon-8.rc` vazio no host-state parece config boa para quem restaurar.
grep -q 'IDS_REGISTRADOS' "$FONTE" ||
	falhou "o backup nao filtra rc por plugin registrado: orfao entra no repo"
grep -q 'rc orfao ignorado' "$FONTE" ||
	falhou "o backup nao denuncia rc orfao"
for f in "$ESTADO"/user/panel/*.rc; do
	[ -e "$f" ] || continue
	id_rc=$(basename "$f" .rc)
	id_rc=${id_rc##*-}
	grep -q "plugin-$id_rc\"" "$ESTADO/user/xfce4-panel.xml" 2>/dev/null ||
		falhou "rc de plugin nao registrado versionado: $f"
done

# (j) copia sem origem e DENUNCIADA (nunca apagada: poda automatica em
#     diretorio versionado apaga trabalho por conta propria)
grep -q 'copia sem origem' "$FONTE" ||
	falhou "o backup nao denuncia copia que o host nao tem mais"

if [ "$FALHAS" -gt 0 ]; then
	printf '%s falha(s)\n' "$FALHAS" >&2
	exit 1
fi
printf 'test_backup_host_state_sessao: ok (10 propriedades)\n'
