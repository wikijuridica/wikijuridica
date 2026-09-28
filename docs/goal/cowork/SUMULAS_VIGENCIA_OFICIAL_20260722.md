# Regeneração OFICIAL da vigência das súmulas STF + achado fiscal (Súmula 14)

Autor: `claude-cowork-fable` — 2026-07-22. Escopo: substituir o arquivo vetado por fonte
oficial e registrar um achado que **corrige um arquivo já landado**.

## 1. O que foi feito

`data/source-audit/cowork_sumulas_vigencia_20260722.jsonl` (67 súmulas) foi **vetado** pelo
próprio autor por usar `meuvademecumonline.com.br` (agregador não-oficial, abaixo da allowlist
gov.br/jus.br/leg.br) como evidência de vigência. Regenerado em:

**`data/source-audit/cowork_sumulas_vigencia_oficial_20260722.jsonl`** (SUBSTITUI o vetado).

Metodologia: 1 fetch ao vivo por súmula na **ficha oficial do LexML Brasil** (`lexml.gov.br`,
gov.br), padrão `urn:lex:br:supremo.tribunal.federal:sumula:1963-12-13;N`. O campo `Súmula` da
ficha é o enunciado canônico do STF (baseSumulas). As 67 súmulas foram buscadas ao vivo (13
diretas nesta sessão + 54 por subagente + S.14 confirmada direta); nenhuma falha de fetch.

## 2. Escopo HONESTO do que a fonte prova (fail-closed)

- **TEXTO**: verificado oficial (LexML) para as 67 → `texto_status="verificado_oficial_lexml"`.
  Isso reancora os enunciados que antes vinham do agregador.
- **VIGÊNCIA**: só afirmada onde há sinal real:
  - **S.152 — revogada**: o LexML traz `(REVOGADA)` **inline no próprio texto oficial**.
  - **S.14 — cancelada**: ver achado abaixo.
  - **Demais 65 — `nao_verificada_em_fonte_oficial_de_status`**: o LexML confirma o TEXTO, não o
    status de vigência. **Não presumi vigência.**

## 3. ACHADO FISCAL (corrige arquivo landado) — Súmula 14

O texto oficial da S.14 no LexML é *"NÃO É ADMISSÍVEL, POR ATO ADMINISTRATIVO, RESTRINGIR, EM
RAZÃO DA IDADE, INSCRIÇÃO EM CONCURSO PARA CARGO PÚBLICO"* e **NÃO traz** `(REVOGADA)/(CANCELADA)`
— diferente da S.152, que traz `(REVOGADA)`. Contudo, fontes secundárias concordantes + a nota
interna anterior indicam que a **S.14 está cancelada, substituída pela Súmula 683/STF** (limite de
idade em concurso só se legitima pela natureza do cargo — art. 7º, XXX, CF).

Consequências:

1. **Correção metodológica importante**: *silêncio de anotação no LexML NÃO estabelece vigência.*
   A S.14 está cancelada e o LexML **não** mostra o marcador. Logo, o primeiro cut deste trabalho
   (que rotularia 65 súmulas como "vigente_formal" por ausência de marcador) foi **descartado** —
   teria repetido a classe de erro do arquivo vetado (presumir vigência de sinal insuficiente).

2. **Erro em arquivo JÁ LANDADO**: `data/source-audit/cowork_sumulas_stf_recheck_20260722.jsonl`
   (landado) traz, para a S.14, `note` afirmando *"súmula CANCELADA (RE 74.486), substituída pela
   Súmula 683"*. O **fato** (cancelada/substituída) tem respaldo, mas o **RE citado diverge entre
   fontes**: vetado e uma fonte web dizem `RE 74.486`; outra fonte web diz `RE 74.355` — ambas
   06/12/1973. **Não publicar o número do RE sem confirmação no portal STF.**

## 4. Ação pedida ao terminal (Claude Code)

- Consumir `cowork_sumulas_vigencia_oficial_20260722.jsonl` como **insumo de TEXTO oficial**
  (substitui o vetado; o vetado permanece na história com DO-NOT-CONSUME).
- Para qualquer página que cite vigência/cancelamento de súmula STF, **checar o portal STF
  baseSumulas item a item** (JS-rendered; requer browser) — LexML não basta para status.
- Confirmar o acórdão de cancelamento da S.14 (RE 74.486 **vs** 74.355) antes de qualquer
  publicação que o mencione. Corrigir o `note` da S.14 no recheck landado nesse momento.

## Proveniência
Fonte: LexML Brasil (gov.br), fichas oficiais por URN; corroboração de status da S.14 por busca
web (portal STF + secundárias). Metadata-only; nenhum corpo de conteúdo oficial copiado para o
produto. Sem edição de shard v2/JSONL de terceiros.
