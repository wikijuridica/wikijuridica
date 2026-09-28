---
name: ler-gigante
description: Use quando precisar consultar um arquivo grande do repositório, como CHECKPOINT.md, AGENTS.md ou GOAL.md.
---

# Ler arquivo gigante

Ler um destes arquivos inteiro queima o contexto da sessão e não deixa espaço
para o trabalho. Ler **por seção** é a única forma sancionada.

## Tamanhos reais (medidos com `stat -c %s`)

| arquivo | bytes | observação |
|---|---|---|
| `/opt/wiki/CHECKPOINT.md` | 2.464.348 | ~616k tokens — **PROIBIDO ler integral** |
| `/opt/wiki/AGENTS.md` | 169.192 | contrato permanente de engenharia |
| `/opt/wiki/GOAL.md` | 142.528 | objetivo do ciclo |
| `/opt/wiki/docs/goal/CHECKPOINT_DIGEST.md` | 8.880 | **comece por aqui** |

**Atenção ao caminho:** o `CHECKPOINT.md` integral fica na **raiz do repo**, não
em `docs/goal/`. Em `docs/goal/` mora só o `CHECKPOINT_DIGEST.md`. Citar
`docs/goal/CHECKPOINT.md` aponta para arquivo inexistente.

## Passo 1 — o digest resolve quase sempre

```bash
cat docs/goal/CHECKPOINT_DIGEST.md
```

8,8 KB, feito para ser lido inteiro. Só desça ao integral se o digest não
responder.

## Passo 2 — índice antes de qualquer leitura

```bash
cd /opt/wiki && grep -n '^## ' CHECKPOINT.md | head -20
```

Devolve número de linha + título das 20 entradas mais recentes (o arquivo tem
387 seções). O número de linha é o endereço para o passo 4.

## Passo 3 — bloco recente sem abrir o arquivo

```bash
cd /opt/wiki && awk '/^## /{n++} n>6{exit} {print}' CHECKPOINT.md
```

Imprime as 6 primeiras seções e **para**. Troque o `6` pelo número de entradas
que quiser.

## Passo 4 — a seção exata, pelo intervalo do índice

```bash
cd /opt/wiki && sed -n '5,13p' CHECKPOINT.md
```

Use o número da linha da seção desejada até a linha da seção seguinte menos um,
ambos vindos do passo 2.

## NUNCA use `tail`

As entradas novas ficam no **TOPO**. Verificado no arquivo: a linha 5 é
`## 2026-07-23`, enquanto as linhas 7243 e 7266 são `## 2026-06-22` e
`## 2026-06-28`. O fim do arquivo é **legado de dois meses atrás**.

`tail -100 CHECKPOINT.md` devolve o estado mais antigo do projeto com cara de
estado atual — é a forma mais rápida de tirar uma conclusão errada sobre o que
está acontecendo hoje.

## Para AGENTS.md e GOAL.md

Mesma disciplina, tamanho menor:

```bash
cd /opt/wiki && grep -n '^## \|^# ' AGENTS.md | head -40
cd /opt/wiki && sed -n '<inicio>,<fim>p' AGENTS.md
```

Precisando de um assunto específico, localize primeiro e leia só o entorno:

```bash
cd /opt/wiki && grep -n 'paid.intent' AGENTS.md | head
cd /opt/wiki && awk 'NR>=1200 && NR<=1260' AGENTS.md
```

## Regras

1. Leitura orçada, sempre: `head`, `sed -n`, `awk` com condição de parada.
2. Nunca `cat` nem leitura integral do `CHECKPOINT.md` — nem "só para conferir".
3. Nunca `tail` em arquivo append-no-topo.
4. Precisando varrer o arquivo todo, delegue a um subagente com escopo estreito,
   e peça de volta a conclusão, não o conteúdo.
5. O `grep -n` já é a leitura barata: em geral o número da linha mais 5 linhas de
   contexto responde a pergunta sem abrir nada.
