# PROMOTE_REDTEAM_20260722 — Verdict adversarial do Cowork Fable 5 (pré-promote)

Autor: `claude-cowork-fable` (Fable 5, papel de crítico adversarial do contrato).
Amostra: 12 páginas de 12 famílias distintas (seed determinístico 20260722), 8 corpos lidos na íntegra,
incluindo 3 shards `codex-*`. Método: leitura humana-adversarial completa (não check automatizado).

## Verdict: APTO PARA PROMOTE (cohort ~250), com 2 correções executáveis não-bloqueantes

A amostra está muito acima de doorway/template. Evidências:

- **Conteúdo jurídico real e específico**: art. 422 CC (boa-fé), REsp 1.709.727/SE (buraco na via,
  responsabilidade subjetiva na omissão — correto), Decreto 21.981/1932 (leiloeiro/matrícula na Junta),
  Lei 11.347/2006 (tiras de glicemia), art. 1.991 CC (inventariante). Nada inventado detectado.
- **Anti-molde**: aberturas variadas (cenário concreto, resposta direta, definição), headings específicos
  por página, nenhuma estrutura repetida entre as 8 lidas — inclusive entre shard "claude" e "codex".
- **Ética OAB (Prov. 205/2021)**: sóbrio, sem promessa ("sem prometer recuperação automática",
  "devolução em dobro não é automática"); jornada digital citada como modo de atendimento ✓.
- **Lanes corretas**: informativas sem CTA comercial; comerciais com sinal de contratação particular
  NO CORPO (ex.: "advogado de sucessões contratado de forma particular") ✓ paid-intent.
- **Titles ≤65 e metas 70–160** em toda a amostra ✓.

## Defeitos encontrados (correção executável, fila de revisão)

1. **`banc-golpe-falso-leilao-veiculos`** (bancario-02): no §"O leiloeiro imitado…", a expressão
   "resultado orgânico" repete 3× em 4 frases consecutivas — clunky, cheiro de reescrita parcial.
   Reescrever o parágrafo variando a referência. ADICIONALMENTE: a página afirma efeitos do Tema 987/STF
   "desde 5 de agosto de 2025" e encerramento de embargos "em 2026" — claims pós-cutoff que DEVEM constar
   de `data/source-audit/citacoes_pos_cutoff_verificacao_*.md`; se não constarem, verificar antes de promover
   esta página específica.
2. **`saude-forn-12-sus-tiras-glicemia-insumos`** (saude-inf1): o §2 diz "A portaria federal fixa o
   direito" sem NOMEAR a portaria — referência vaga para claim específico. Nomear (ou reformular para
   "a regulamentação federal") e conferir a URL da fonte 2 (path duplicado `/tratamento/tratamento/`).

## Fontes stale — resolvido pelo Cowork (insumo pronto)

As 391 rejeições `official_source_http_status_invalid`/`verified_at_invalid` foram re-verificadas AO VIVO
em 2026-07-22: **120 URLs únicas, 119 OK, 1 REPROVADA** (`gov.br/saude/.../agua` → redireciona para login;
substituir fonte). Causa-raiz: redatores não rodaram verificação (`verified_at` vazio) + sites
client-rendered (noticias.stf.jus.br, portal.stf.jus.br, in.gov.br) e CAPTCHA (gov.br/mec) derrubam
verificador curl — **não são fontes mortas**. Consumir:

- `data/source-audit/cowork_source_recheck_20260722.jsonl` (por URL, com verdict/título/nota/método)
- `data/source-audit/cowork_source_recheck_20260722_pages.jsonl` (por intent×source_index — 390/391 ok)

Recomendação de engenharia para o verificador vivo (`audit-v2-source-provenance --live`): classificar
domínios client-rendered conhecidos como `verified_via=cowork_live_browser` em vez de reprovar por status 0;
lista dos domínios afetados está nas notas do JSONL.

## Alertas de indexação (para o gate HTML/SEO, não bloqueiam cohort-1)

- `l10406.htm` (Código Civil NÃO-compilado) serve meta noindex; páginas que citam essa versão devem
  preferir `l10406compilada.htm` (o recheck marca as afetadas).
- `l7347orig.htm` é a versão original da LACP; há compilada disponível — preferir em revisão futura.
