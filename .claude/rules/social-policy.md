---
paths:
  - "content/social_policy.json"
  - "internal/socialpolicy/policy.go"
  - "cmd/social/**/*.go"
  - "cmd/generate-social-kek/**/*.go"
  - ".env.social"
  - ".env.local"
---

# `social_policy.json` — campo novo aqui antes do binario novo = laco de boot

Memorias de origem: `social-policy-campo-novo-exige-binario.md`,
`social-kek-mora-em-env-social.md`.

`internal/socialpolicy.Load` decodifica com `decoder.DisallowUnknownFields()`.
`cmd/social/main.go` faz `log.Fatalf` quando a politica reprova. A unit
`wikijuridica-social` tem `Restart=always` + `RestartSec=5`.

Somando os tres: **um campo que o binario VIVO nao conhece transforma o proximo
restart em laco de boot da rede social.** Aconteceu em 2026-09-09 com
`habitualidade_modo`. O mesmo vale para valor que a validacao antiga reprova —
`destrava_abrir_thread: 0` com `inicial: 0` cai em
`social_policy_destrava_sem_custo`.

A politica e' lida **uma vez, no boot**, e o binario vivo pode ser de dias antes
do worktree. `deploy-publico` (com REBUILD=1, que e' o default) troca e
reinicia o social sem olhar este JSON.

## Antes de tocar este arquivo

```
git show HEAD:internal/socialpolicy/policy.go | grep -n DisallowUnknownFields
```

e leia a validacao vigente. Campo ou valor que o binario vivo recusa so entra no
disco **no mesmo passo** em que o binario novo sobe:

```
build → swap do binario → editar o JSON → sudo -n systemctl restart wikijuridica-social
      → conferir /readyz e o journal
```

Quem mais carrega a politica: `cmd/moderacao-revisar-prazos` (compilado a cada
execucao por `tools/run-moderacao-revisar-prazos`) e `cmd/generate-social-temas`.

## A KEK do social mora SO em `.env.social`, e a mensagem do codigo ja mentiu

Em 2026-09-09 a mensagem de `cmd/generate-social-kek` e de `cmd/social/conta.go`
mandava "colar em `.env.local`"; a KEK nova foi colada la (12:53) e o CLI
`social-verificar-oab` foi documentado com `--env-file /opt/wiki/.env.local`.
Medido depois pelo `/proc/<MainPID>/environ` do `wikijuridica-social`: o hash da
KEK efetiva era o de `.env.social` (chave de 2026-09-05), porque a unit declara
`EnvironmentFile=-/opt/wiki/.env.local` e, **por ultimo**,
`EnvironmentFile=-/opt/wiki/.env.social` — o systemd deixa a ultima vencer. A
chave de `.env.local` nunca cifrou nada; o CLI com `--env-file .env.local` teria
criado a conta do dono com chave que o servidor nao usa (conta ilegivel) e
`--conferir-email` falharia. Corrigido: mensagens, ajuda da flag, testes e doc
apontam `.env.social`, e a linha morta saiu de `.env.local`.

O desenho e' **isolamento de processo** (comentario da unit): o `cmd/server`, que
serve o acervo a todo bot, tambem carrega `.env.local`, e a KEK que cifra e-mail
e deriva o indice cego do login nao pode entrar no ambiente dele. O
`socialisolation` so ve literal de codigo, nao variavel de ambiente — a separacao
de arquivos e' a metade da trava que o gate nao alcanca.

Na pratica: (1) segredo do social vai em `.env.social`, nunca em `.env.local`;
(2) antes de afirmar qual segredo um processo usa, medir pelo
`/proc/<pid>/environ` (so o hash, nunca o valor) — mensagem de codigo e memoria
de sessao sao alegacao; (3) o backup (`tools/generate-backup-wiki`) copia os dois
arquivos para `segredos/`, e a data da copia se confere depois de trocar
qualquer um.
