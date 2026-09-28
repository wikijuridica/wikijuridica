# MOLD_ADJUDICATION_ADDENDUM_20260722 — cidadania-04, bancario-r02, seguros-r02

Autor: `claude-cowork-fable` (subagente adjudicador). Complemento de `MOLD_ADJUDICATION_20260722.md`.
Método: leitura INTEGRAL de todas as páginas reais dos 3 shards (2+3+5 = 10 páginas) + interseção
objetiva de 8-grams entre pares de páginas por shard. Nenhum shard foi editado.

## 1. cidadania-04 (90,91%, n=22) — FALSO-POSITIVO (bug do measurement)

O shard tem **apenas 2 páginas reais**; as outras **20 linhas são registros de skip por allowlist**
(`skipped: true`, `skip_reason` = normattiva.it/dre.pt/boe.es/gesetze-im-internet.de fora do allowlist
gov.br/jus.br/leg.br/mp.br), **sem corpo**. O measurement contou os skips como páginas de sequência
vazia: `seq: []` dominante em 20/22 = 90,91% exatos. Artefato puro de medição.

Entre as 2 páginas reais (`cid-naturalizacao-ordinaria-requisitos` × `cid-naturalizacao-extraordinaria-15-anos`),
o ÚNICO 8-gram compartilhado é fato legal legítimo (classe que o validate.go já exime, cf. e9905e06):
> "publicação do ato no Diário Oficial da União"

Conteúdo diferenciado (art. 65 vs art. 67 da Lei 13.445/2017; prazos 4/2/1 anos vs 15 anos; art. 233 §2º
vs art. 238 §2º), páginas complementares com cruzamento correto. Ressalva menor, SEM fila: ambas abrem
com o mesmo dispositivo narrativo de persona ("Um engenheiro venezuelano chega ao Brasil…" /
"Uma boliviana que veio ao Brasil ainda jovem…") e fecham na causa (b) branda — variar se o lote
cidadania crescer. **Ação: nenhuma reescrita; corrigir o gerador do measurement para excluir `skipped`.**

## 2. bancario-r02 (100%, n=3) — sinal do measurement é ARTEFATO; molde real APENAS causa (b), baixa severidade

Os 100% são triviais: n=3 e as 3 páginas têm 5 seções de heading único → bucket `outro` ×5 idêntico
por construção. **Zero 8-grams compartilhados entre qualquer par** — corpo genuinamente diferenciado
(art. 333 CC / MP 2.200-2 + Lei 14.063 + Tema 1.061 STJ / Res. CMN 4.860). NÃO é candidato a reescrita
estrutural. O único molde real é a **fórmula de fechamento comercial (causa b)**, 3/3 páginas:
> `banc-acordo-quebrado-vencimento-antecipado`: "…medida judicial adequada, **sem garantia de suspensão ou desconto**."
> `banc-assinatura-eletronica-contrato-nao-reconheco`: "O profissional deverá verificar autoria, integridade, disponibilização do crédito e prejuízo, **sem prometer nulidade ou indenização**."
> `banc-banco-digital-sem-atendimento-onde-reclamar`: "**Não há garantia de liminar ou indenização.**"

Padrão acessório: 6/9 respostas de FAQ abrem com "Não"(-variante). **Spec (micro-edição, formato
`v2_mold_rewrite_specs`, `obs: "corpo preservado; só fechamento e FAQ"`):** por página, variar ≥2 dos
4 eixos do fechamento definidos na adjudicação-mãe (abertura do parágrafo final, canal, verbo de
garantia, cláusula de dependência); máx. 1 resposta de FAQ por página iniciando por "Não" seco.
Sem retitulação (`headings_novos` = vazio; headings atuais são bons e únicos).

## 3. seguros-r02 (80%, n=5) — MOLDE REAL: causa (b) 5/5 + causa NOVA (d) "módulo argumentativo clonado" 4/5

Headings únicos (o 80% vem do bucket `outro`×6), mas a leitura integral confirma duas camadas reais:

**Causa (b) — fechamento comercial, 5/5 páginas**, com par quase-verbatim:
> `seg-auto-negativa-recusa-bafometro`: "Advogado pode revisar contrato e prova remotamente, **sem prometer indenização**."
> `seg-residencial-furto-sem-arrombamento`: "Advogado pode revisar negativa e prova **sem prometer indenização**."
> `seg-prestamista-banco-cobra-apos-obito`: "Advogado ou Defensoria pode revisar inventário, contrato e seguro **sem prometer quitação**."
(+ `seg-auto-sinistro-fora-area-cobertura` "sem prometer cobertura"; `seg-residencial-joias-valores-excluidos` "não garante resultado").

**Causa (d) — NOVA: módulo argumentativo intertemporal da Lei 15.040 clonado em 4/5 páginas**
(bafometro, furto, joias, prestamista), sempre no mesmo slot (penúltima/última seção), com o esqueleto
[vigente desde 11/12/2025] + [a data do sinistro sozinha não decide] + [ato jurídico perfeito] +
[art. 134 não contém transição geral]. Evidência verbatim (8-grams joias×prestamista):
> "A Lei 15.040 vigora desde 11 de dezembro de 2025"
e o clone parafrástico do arremate, 4 páginas distintas:
> bafometro: "Não presuma uma transição geral que o art. 134 da Lei 15.040 não escreveu"
> furto: "…preserve o ato jurídico perfeito, sem inventar transição geral no art. 134"
> joias: "Preserve o ato jurídico perfeito e não atribua ao art. 134 uma transição geral inexistente"
> prestamista: "…preservar o ato jurídico perfeito, sem criar uma regra geral de transição que não consta do art. 134"

A frase-fato ("Lei 15.040 vigora desde…") isolada seria isenta como citação legal (e9905e06); o
RACIOCÍNIO completo repetido em 4 páginas é molde editorial, não citação. Camada acessória: o slot de
canais "Susep / consumidor.gov.br / Procon" aparece nas 5 páginas com a trinca embaralhada.

**Spec executável (formato `v2_mold_rewrite_specs`, micro-edição, corpo preservado):**
- `headings_novos` = vazio (headings bons); NÃO reescrever conteúdo jurídico — o módulo intertemporal é
  correto e útil; o problema é a clonagem.
- Des-clonar causa (d): manter a análise intertemporal COMPLETA em exatamente 1 página do lote
  (sugestão: `seg-auto-negativa-recusa-bafometro`, que já tem seção dedicada "Faça a análise
  intertemporal completa"); nas outras 3, comprimir para 1 frase própria da página (≤25 palavras,
  ancorada no fato da página: furto→data do furto, joias→data do sinistro/declaração,
  prestamista→data do óbito/atos) + `internal_link_topics` apontando para a página com a análise
  completa. Proibido repetir "ato jurídico perfeito" e "transição geral"+"art. 134" em >1 página do lote.
- Causa (b): variar ≥2 dos 4 eixos do fechamento entre as 5 páginas (regra da adjudicação-mãe);
  proibido "sem prometer <substantivo>" como sintagma final em >2 das 5.
- Trinca de canais: citar só o canal pertinente ao caso concreto em ≥2 páginas (Susep para negativa
  de cobertura; consumidor.gov.br para interlocução documentada), em vez da trinca completa 5×.
- Gate de saída: interseção de 8-grams entre pares (excluída a classe de citação legal isenta) = 0;
  fechamentos com similaridade ≤0.60.

## 4. Regeneração da fila por percentil — reforço com estes números

A adjudicação-mãe já pediu; estes 3 shards provam o porquê com números: **90,91% (cidadania-04) era
20 skips contados como páginas; 100% (bancario-r02) era n=3 no bucket `outro`; e o único molde real
do trio (seguros-r02) não é o que o classificador mediu** (headings únicos — o molde está em slot de
fechamento e módulo clonado). Regenerar `v2_mold_rewrite_queue` com: (i) exclusão de registros
`skipped` ANTES do cômputo; (ii) n mínimo por shard (n≥8) para `dominant_seq_pct` valer como sinal;
(iii) detector complementar de molde de 2ª ordem: 8-grams repetidos entre páginas fora da classe de
citação legal isenta + similaridade de fechamento/slot — foi isso, não a sequência de headings, que
separou molde real de falso-positivo nestes 3.
