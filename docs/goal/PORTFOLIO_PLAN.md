# PORTFOLIO_PLAN.md — Distribuição-alvo do portfólio v2 (DEC-007)

Metas por área (teto, não obrigação — inflar com permutação é proibido). Total-alvo de candidatos: ~10.700 para selecionar 10.000 (P0) e semear a expansão para 100k (P1).

| # | Área (`practice_area`) | Arquivo | Meta | Ondas |
|---|---|---|---|---|
| 1 | trabalhista | portfolio_v2/trabalhista.jsonl | 400 | piloto |
| 2 | saude (suplementar) | portfolio_v2/saude.jsonl | 350 | piloto |
| 3 | glossario (verbetes) | portfolio_v2/glossario.jsonl | 350 + 1050 | piloto + 3 ondas |
| 4 | previdenciario (comercial; BPC/LOAS informativo) | portfolio_v2/previdenciario.jsonl | 650 | 2 ondas |
| 5 | consumidor (geral: compras, serviços, garantia, educação privada) | portfolio_v2/consumidor.jsonl | 700 | 2 ondas |
| 6 | bancario (fraudes, consignado, juros, negativação, Pix) | portfolio_v2/bancario.jsonl | 700 | 2 ondas |
| 7 | familia (divórcio, guarda, pensão, união estável) | portfolio_v2/familia.jsonl | 550 | 2 ondas |
| 8 | sucessoes (inventário, testamento, partilha, ITCMD) | portfolio_v2/sucessoes.jsonl | 400 | 1 onda |
| 9 | imobiliario (locação, compra e venda, condomínio, usucapião, registro) | portfolio_v2/imobiliario.jsonl | 700 | 2 ondas |
| 10 | aereo-consumidor (voos, bagagem, pacotes, hospedagem) | portfolio_v2/aereo.jsonl | 300 | 1 onda |
| 11 | telecom-energia (telefonia, internet, TV, energia elétrica, água) | portfolio_v2/telecom_energia.jsonl | 350 | 1 onda |
| 12 | lgpd-dados (titular de dados, vazamentos, ANPD) | portfolio_v2/lgpd.jsonl | 300 | 1 onda |
| 13 | inpi-pi (marcas, patentes, direitos autorais, software) | portfolio_v2/inpi.jsonl | 300 | 1 onda |
| 14 | tributario-pj-mei (MEI, Simples, autuações, parcelamentos, CND) | portfolio_v2/tributario.jsonl | 450 | 1 onda |
| 15 | empresarial-contratos (B2B, sociedades, prestação de serviços, inadimplência PJ) | portfolio_v2/empresarial.jsonl | 450 | 1 onda |
| 16 | seguros (vida, auto, residencial, prestamista, DPVAT/SPVAT, SUSEP) | portfolio_v2/seguros.jsonl | 350 | 1 onda |
| 17 | transito (multas, CNH, apreensão de veículo, acidentes) | portfolio_v2/transito.jsonl | 300 | 1 onda |
| 18 | servidor-publico (concursos, estágio probatório, processos disciplinares, direitos) | portfolio_v2/servidor.jsonl | 250 | 1 onda |
| 19 | procedimentos (gov.br, Meu INSS, consumidor.gov.br, e-notariado, juizados, certidões) | portfolio_v2/procedimentos.jsonl | 500 | 1 onda |
| 20 | previdenciario-informativo (BPC/LOAS e assistencial — lane informativa) | portfolio_v2/previdenciario_informativo.jsonl | 150 | 1 onda |

Regras de consolidação:
- Merge final em `data/editorial/authorial_mass_intent_portfolio_v2.jsonl` com dedupe global de `intent_id` e de `long_tail_query` normalizada (checagem cruzada entre áreas: ex. "plano de saúde" só na área saude; "seguro saúde" = saude, não seguros; multas de trânsito ≠ consumidor).
- Cada área passa por revisão de amostra (leitura minha, como advogado) antes de liberar a redação em massa.
- Seleção P0 = 10.000 por cobertura equilibrada (caps por família/cluster), o excedente fica governado para P1.
