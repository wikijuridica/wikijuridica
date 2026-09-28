# SOURCE_RESEARCH_PENDING_104 — Diagnóstico e destrave (Cowork Fable 5, 2026-07-22)

Autor: `claude-cowork-fable`. Fonte: `data/ops/v2_ingest_report.jsonl` (run 20260718) + leitura de 8 páginas
+ varredura de tools/. Fila: 104 rejeições `source_unverified_research_pending`.

## Achado central: 96/104 (92%) É BUG DE FLAG, NÃO FONTE FALTANDO

As 96 páginas têm `official_sources` COMPLETOS e 100% verificados (`verified_at` 2026-07-16,
`http_status:200`) — mas `needs_source_research` continua `true` e o gate
(`internal/v2ingest/validate.go:494`) rejeita SÓ pelo booleano, sem olhar as fontes:

```go
if page.NeedsSourceResearch { reject("source_unverified_research_pending:...") }
```

**Não existe nenhuma ferramenta em tools/ que desligue o flag após verificação** (varri ~540 scripts:
`reconcile_v2_strict_source_stock.py` preserva verified_at/http_status mas não toca o flag). O laço
"fonte verificada → flag off" nunca foi fechado. Rodada de verificação de 2026-07-16 carimbou as fontes
e deixou o booleano órfão.

## Correção executável (para o terminal — 2 opções, preferir a 1)

1. **Reconciliador sancionado** (novo `tools/generate-v2-source-research-reconcile`): para página com
   `needs_source_research=true` E todas as `official_sources` com `verified_at` recente + `http_status`
   2xx E contagem de fontes ≥ mínimo do page_type → seta `needs_source_research=false` +
   `source_research_note="reconciled:<data>:all_sources_verified"`. Rodar via canal CAS normal, nunca
   edição manual. Depois: rerun do ingest dry-run → ~96 páginas migram para aceitas.
2. Alternativa menor: gate passa a rejeitar apenas se (flag E ∃ fonte sem verificação) — mantém o flag
   como sinal editorial sem poder de veto quando a evidência o contradiz.

## Composição da fila (104)

- `flag_obsoleto`: **93** (nada a pesquisar; só reconciliar+reingerir)
- `flag_obsoleto+orphan_portfolio`: 3 (reconciliar + remapear intent no portfólio)
- `verificacao_tecnica_bloqueada`: 3 — todas Tema 987/STF (portal.stf/digital.stf falham TLS;
  noticias.stf responde 403 a HEAD). Fonte CERTA; resolver com espelho TLS-válido do desfecho
  (íntegra RTF portal.stf.jus.br/processos/downloadTexto.asp?id=6897493&ext=RTF — já validada no
  cowork_tema987_verificacao_20260722.md — ou DJe). Casa com a recomendação `verified_via=cowork_live_browser`.
- `fonte_insuficiente+orphan_portfolio`: 1 (`saude-exame-genetico-plano-cobertura` — +1 fonte e remapear)
- `descobrir_fonte_nova`: 1 (`ene-afericao-do-hidrometro` — falta resolução de agência estadual de
  saneamento sobre custeio do teste de aferição: ARSESP/AGENERSA/ARSAE/ADASA conforme concessionária)

Por área (top): tributario 16, seguros 14, transito 13, aereo 8, consumidor 7, imobiliario 7,
procedimentos 7. 36 das 104 têm motivo EXTRA independente (15 title_length, 13 dup_phrase, 12 faq
faltando) — corrigir junto na fila de revisão.

## Lista completa

A lista integral `intent_id | shard | tipo | area` (104 linhas) está no transcript do agente desta
sessão Cowork e reproduzida abaixo de forma compacta por serem dados operacionais:

flag_obsoleto (93): aer-animal-suporte-emocional-negado, aer-apagao-ti-sistemico-voos-parados,
aer-assento-duplicado-duas-reservas, aer-assento-quebrado-servico-bordo-vicio,
aer-conexao-tempo-minimo-perdida, aer-doenca-contagiosa-barrado-sanitaria,
aer-no-show-volta-internacional, aer-queda-acidente-terminal,
banc-cartao-chargeback-compra-internacional-nao-entregue, banc-golpe-telefone-falso-google-anuncio,
banc-pix-chave-reivindicada-por-terceiro, banc-pix-por-aproximacao-roubo-contestar,
cons-aluguel-por-temporada-anfitriao-cancelou, cons-bens-digitais-comprados-plataforma-encerrou,
cons-carro-eletrico-autonomia-abaixo-do-anunciado, cons-comprei-de-particular-usados-cdc-nao-aplica,
cons-comprei-de-vendedor-informal-tenho-direitos, cons-conta-jogo-banida-itens-comprados,
cons-conta-plataforma-invadida-nao-recupero-acesso, emp-joint-venture-parceria-empresarial-o-que-e,
emp-responsabilidade-pre-contratual-rompimento-negociacao, emp-seguro-garantia-carta-fianca-diferenca,
fam-alteracao-regime-bens-efeitos-passado, fam-suprimir-sobrenome-pai-ausente-do-filho,
gloss-classificacao-dos-contratos, gloss-pressupostos-processuais, imob-bem-familia-imovel-alugado-renda,
imob-bem-familia-solteiro, imob-bem-familia-terreno-vazio, imob-direito-de-laje-vender-financiar,
imob-hipoteca-imovel-execucao, imob-responsabilidade-tecnica-art-rrt, pi-dominio-ex-prestador-registrou,
lgpd-condominio-expos-inadimplente, lgpd-negativado-por-homonimo,
prev-atestmed-negado-pericia-presencial, prev-converter-b31-em-b91-doenca-do-trabalho,
prev-empresa-contesta-nexo-b91-virou-b31, prev-mei-transportador-aliquota-12,
proc-bo-estelionato-representacao, proc-bo-online-furto-roubo, proc-bo-perda-documentos,
proc-defensoria-agendar-atendimento, proc-justica-leilao-judicial-consultar,
proc-justica-peticionar-documento-parte, proc-medida-protetiva-online, saude-sus-oncologia-prazo-60-dias,
saude-sus-tratamento-fora-domicilio-tfd, seg-auto-negativa-recusa-bafometro,
seg-auto-sinistro-fora-area-cobertura, seg-empresarial-cosseguro-a-quem-cobrar, seg-empresarial-cyber,
seg-empresarial-do-defesa-multa, seg-empresarial-garantia-execucao,
seg-empresarial-negativa-lucros-cessantes, seg-empresarial-todos-riscos-vs-nomeados,
seg-prestamista-banco-cobra-apos-obito, seg-residencial-furto-sem-arrombamento,
seg-residencial-joias-valores-excluidos, seg-sinistro-outro-seguro-mesmo-risco,
seg-transporte-cargas-sinistro, seg-vida-invalidez-inss-reconhece-seguradora-nega,
ene-rodizio-de-agua-desconto, tel-provedor-cessao-carteira-clientes, trab-dano-estetico-acidente,
trab-motorista-agregado, trab-trabalho-familiar, tra-acidente-animal-na-pista-rodovia-pedagiada,
tra-acidente-buraco-na-via-responsabilidade-orgao, tra-entrega-amigavel-veiculo-quita-divida,
tra-liminar-continuar-dirigindo-suspensao-administrativa, tra-multa-carga-mal-acondicionada-caindo,
tra-multa-emergencia-estado-de-necessidade, tra-multa-excesso-peso-balanca,
tra-multa-nao-dar-passagem-veiculo-emergencia, tra-multa-sinalizacao-via-ausente-ou-apagada,
tra-reprovacao-repetida-exame-pratico-cobranca, tra-reprovado-exame-aptidao-detran-contestar,
tra-transporte-clandestino-passageiros-apreensao, tra-veiculo-transporte-escolar-requisitos-multa,
trib-aduana-drawback-suspensao, trib-autuacao-distribuicao-disfarcada-lucros, trib-cnd-cessao-quotas-socio,
trib-compensacao-precatorio-divida-tributaria, trib-crf-fgts-empresa-debito,
trib-icms-st-complemento-venda-maior, trib-icms-st-mva-margem-contestacao,
trib-icms-st-ressarcimento-venda-outro-estado, trib-iptu-isencao-aposentado-baixa-renda,
trib-iptu-progressividade-tempo-nao-edificado, trib-iptu-revisao-valor-venal,
trib-irpj-subvencao-icms-tributacao, trib-parcelamento-previdenciario-empresa,
trib-piscofins-insumo-creditamento-essencialidade, trib-restituicao-inss-acima-teto-multiplos-vinculos,
trib-taxa-lixo-coleta-legalidade
flag_obsoleto+orphan (3): ene-cobranca-demanda-contratada-grupo-a, ene-cobranca-energia-reativa-excedente,
saude-consulta-retorno-cobranca
verificacao_tecnica_bloqueada (3): dig-verbete-responsabilidade-plataforma-conteudo,
pi-responsabilidade-plataformas, imob-golpe-anuncio-falso-aluguel
fonte_insuficiente+orphan (1): saude-exame-genetico-plano-cobertura
descobrir_fonte_nova (1): ene-afericao-do-hidrometro
