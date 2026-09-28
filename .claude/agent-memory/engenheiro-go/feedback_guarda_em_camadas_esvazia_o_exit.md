---
name: guarda-em-camadas-esvazia-o-exit
description: Com guardas em sequência que saem com o mesmo código, asserção por exit code passa verde com a guarda desligada; asserte QUAL guarda falou
metadata:
  type: feedback
---

Em cadeia de guardas sequenciais (validação de disco, de caminho, de
pré-requisito), **exit code não identifica a guarda**: a seguinte recusa a mesma
entrada com o mesmo código. Toda asserção precisa casar a mensagem
DISTINTIVA daquela guarda e, quando as guardas são vizinhas, afirmar também que
a mensagem da guarda seguinte NÃO apareceu.

**Why:** medido em 2026-09-22 nas bancadas do kit de migração (`ops/provisionamento/`).
Três casos concretos:
- `preparar-disco-backup.sh` com a guarda 2 desligada: `/dev/sda1` continuava
  saindo 1, pela guarda 3. Só `nao_contem "essencial:"` pegou.
- `restaurar-etc.sh` com o `exit 2` da captura de `/etc` rebaixado: continuava
  saindo 2, pela guarda do firewall logo abaixo. Só `nao_contem "captura de
  firewall ausente"` pegou.
- Colisão de substring no mesmo arquivo: a linha de APROVAÇÃO da guarda 3 diz
  "nenhum ponto de montagem essencial", e o trecho curto "ponto de montagem
  essencial" casava com ela — a asserção passava verde com a guarda desligada.

**How to apply:** ao escrever asserção sobre script que recusa entrada, (1) case
o trecho que só a recusa daquela guarda imprime — inclua o verbo ("carrega
ponto de montagem essencial"), nunca o substantivo solto; (2) acrescente um
`nao_contem` da guarda vizinha; (3) prove a mordida desligando a guarda numa
cópia e vendo a bancada reprovar — se ela continuar verde, a asserção é
decorativa. Vale igual para teste Go sobre erro sentinela: `err != nil` não diz
qual validação falhou. Ver [[feedback_medir_com_a_regua_do_pacote]] e
[[feedback_mutante_vivo_terceiro_desfecho]].
