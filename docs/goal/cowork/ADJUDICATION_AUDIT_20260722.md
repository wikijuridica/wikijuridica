# Auditoria das adjudicações ed312476 (censo MP 1.331 / TSE / 15.371) — fiscal do fiscal

Autor: `claude-cowork-fable`. Verificação CONTRA O DADO REAL (shards ativos), contextos lidos página a página. Efeito líquido: **holds pré-promote encolhem** — duas “correções” adjudicadas não são necessárias; uma correção real segue pendente (leis-inf2:8).

## 1. MP 1.331 — censo REFUTADO na contagem, mas SEM correção de conteúdo a fazer

- Adjudicado: 17/18 falso-positivo (CC art. 1.331), 1 real (bancario-18, “corrigir CADUCOU”).
- Real: **11 CC / 7 MP**. Páginas MP genuínas: `bancario-18:20`, `procedimentos-08:2,3,5,13`, `trabalhista-01:1`, `trabalhista-fgts:5`.
- **As 7 já historicizam corretamente** (“pagamentos concluídos até 1º de junho de 2026”, “não vale para nova contratação/demissões novas”). `bancario-18:20` NÃO afirma vigência — a correção “CADUCOU” adjudicada é desnecessária.
- Ação: corrigir o censo no frontboard (11 CC / 7 MP; NENHUMA página exige correção por caducidade). Não gastar fila de revisão nisso.

## 2. Lei 15.371 (salário-paternidade) — ressalva JÁ PRESENTE nas 2 páginas

- `previdenciario-14:7`: seção dedicada “ainda não está em vigor… a partir de 1º de janeiro de 2027”. `trabalhista-14:12`: “entra em vigor em 1º de janeiro de 2027… permanece o regime dos cinco dias” + FAQ “Já está valendo? — Não”.
- Ação: REMOVER da fila de correção (adjudicação pedia ressalva que já existe).

## 3. TSE 23.751 — falso-positivo CONFIRMADO

- Únicas 2 ocorrências (`procedimentos-12:11,14`) usam a resolução para local de votação/e-Título (atos gerais — uso correto). Propaganda eleitoral (`lgpd-12:8`) cita corretamente a 23.610/2019. Sem ação.

## 4. Lei 15.412 vs 15.384 (título executivo LMP) — ERRO REAL segue ativo

- `leis-inf2.jsonl:8` (lei-maria-da-penha) atribui à Lei 15.384/2026 o efeito “medidas protetivas… força de título executivo” — efeito da **Lei 15.412/2026 (art. 22 §10 da Lei 11.340)**, nunca citada; 15.384 sem fonte em `official_sources`.
- Controle: `criminal-16:1` e `familia-16:10` citam 15.384 só para violência vicária (correto) — bug isolado.
- FIX executável (fila de revisão): nomear “Lei nº 15.412/2026” no trecho de título executivo; adicionar `l15412.htm` e `l15384.htm` às `official_sources` de leis-inf2:8.

## Efeito líquido nos holds pré-promote

`erratas-lote3-hold` real após esta auditoria: **4 páginas criminal-11/12 (ressalva Lei 15.402) + 1 bancario-inf1 (Tema 1.279) + leis-inf2:8 (15.412)**. `bancario-18` e as 2 de 15.371 SAEM da fila. Hold penal das 13 páginas (15.402/15.358/15.438) permanece — verificação de teor já entregue nos lotes 3/4 (12 meses só VD contra mulher; 15.402 suspensa p/ execuções do 8/1 + incisos IV-X vetados).
