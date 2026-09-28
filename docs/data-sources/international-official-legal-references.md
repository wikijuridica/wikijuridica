# Referências jurídicas oficiais internacionais

Este registro cobre apenas URLs oficiais específicas usadas como proveniência
de conteúdo autoral sobre relações jurídicas internacionais de transporte,
telecomunicações, cidadania e nacionalidade. Ele não autoriza
coleta em massa, espelhamento, armazenamento de texto oficial nem publicação
automática.

## Superfícies oficiais exatas

Coorte de transporte e telecomunicações consolidada em 2026-07-13:

- OACI (`www.icao.int`): tratado e limites de responsabilidade da Convenção de
  Montreal, com cobertura restrita ao documento e ao caminho jurídico oficial.
- Publications Office Cellar (`publications.europa.eu`): o HTML oficial do
  Regulamento (CE) nº 261/2004 e o PDF oficial das orientações de 2024 foram
  localizados por identificadores Cellar estáveis; ambos responderam `200`.
- OEIL do Parlamento Europeu (`oeil.europarl.europa.eu`): o procedimento
  `2013/0072(COD)` respondeu `200`. Em 2026-07-13, a ficha registrava aprovação
  do texto conjunto pelo Parlamento em terceira leitura em 2026-07-07, mas
  ainda aguardava a decisão final do Conselho; nenhum ato final publicado foi
  localizado. Alegações de vigência exigem refresh, não inferência.
- Your Europe (`europa.eu`): orientação institucional específica sobre direitos
  dos passageiros e entrada de viajantes.
- GovInfo (`www.govinfo.gov`): publicação oficial do Federal Register dos EUA,
  limitada aos pacotes específicos. A regra federal de reembolso de 2024
  continua sendo a referência normativa. O notice FR 2026-13675, publicado em
  2026-07-07, registra política temporária de enforcement até 2027-07-07 apenas
  para a mera renumeração do voo acompanhada de reacomodação do passageiro,
  sem mudança ou atraso significativo. O notice não revoga a regra nem alcança
  cancelamento ou alteração significativa.
- SUBTEL Chile (`www.subtel.gob.cl`): referência institucional restrita ao
  artigo oficial sobre o roaming Brasil-Chile, cuja aplicação foi informada
  pela autoridade chilena como iniciada em 2023-07-25, inclusive os limites
  divulgados de 90 dias contínuos ou 120 dias não contínuos no mesmo ano. O
  registro não aprova o host inteiro, não substitui a norma brasileira nem
  permite extrapolar condições do contrato e o alcance territorial da medida.

Expansão autorizada pelo dono em 2026-07-15, restrita a metadados e ainda
bloqueada para publicação:

- Diário da República Eletrônico de Portugal (`diariodarepublica.pt` e
  `dre.pt`): legislação portuguesa oficial, inclusive a Lei da Nacionalidade.
- BOE da Espanha (`www.boe.es`): legislação espanhola publicada pela agência
  estatal do boletim oficial.
- Normattiva (`www.normattiva.it`): legislação italiana consolidada oficial.
- Gazzetta Ufficiale (`www.gazzettaufficiale.it`): diário oficial italiano. A
  resposta `404` em `robots.txt` registra ausência do documento naquele
  caminho; não concede permissão de coleta.
- Gesetze im Internet (`www.gesetze-im-internet.de`): legislação federal alemã
  oficial.
- ISAP do Sejm (`isap.sejm.gov.pl`): atos jurídicos oficiais da Polônia.
- MAECI (`www.esteri.it`): orientação consular italiana. O WAF Radware pode impedir
  a verificação automática; resposta do WAF ou redirecionamento não comprova o
  conteúdo jurídico.
- EUR-Lex (`eur-lex.europa.eu`): direito oficial da União Europeia. O host foi
  readmitido na lista exata pela decisão de 2026-07-15, mas o `202` ambíguo de
  `HEAD`/`GET` simples continua sem valor probatório: cada uso exige URL de ato
  específico que a proveniência consiga confirmar, sem inferir vigência.
- Portal das Comunidades Portuguesas (`portaldascomunidades.mne.gov.pt`):
  orientação consular oficial de Portugal.

A autorização desses hosts só permite que as ferramentas tentem validar uma
URL oficial específica. Ela não aprova o host inteiro, não transforma `202`,
WAF, redirecionamento, `403` ou `404` em evidência, não libera scraping ou
cópia e não abre `ingestion_enabled`, `publication_allowed`, renderização,
sitemap ou aprovação. Enquanto a proveniência live do documento exato e os
demais gates não passarem, os registros permanecem metadata-only e bloqueados.
Para o Regulamento 261 e as orientações de 2024, o manifest exato do Cellar com
resposta válida continua sendo a referência preferida; para o estado da
reforma, permanece necessária a ficha exata do OEIL.

## Termos e robots separados da fonte jurídica

Os metadados de uso da coorte original foram atualizados separadamente em
2026-07-14:

- termos da OACI: `200`;
- aviso legal do Publications Office: `403`; o refresh de `robots.txt` de
  `publications.europa.eu` terminou em `network_error` e permaneceu bloqueado
  (a auditoria anterior havia observado redirecionamento para `op.europa.eu` e
  resposta `403`);
- aviso legal do Parlamento Europeu: `200`; o `robots.txt` do host OEIL
  respondeu `404`;
- aviso legal da União Europeia ligado no rodapé do Your Europe: `200`;
- políticas do GovInfo: `200`.
- termos de uso da SUBTEL: `200`, mas a própria página mantém escopo histórico
  ligado ao blog; o resultado não foi generalizado para todo o portal;
- `robots.txt` da SUBTEL: `200` com `Content-Type: text/html`, portanto tratado
  como resposta HTML inválida para um documento robots e mantido bloqueado.

Os resultados `403` e `404` são estados restritos registrados honestamente,
não sucessos nem permissões implícitas. O campo `terms_url` aponta para o aviso
ou a política real, nunca para o ato usado como fonte. Um host presente apenas
em `terms_url` ou `robots_url` não amplia os domínios aceitos para conteúdo
jurídico.

Para os nove registros de 2026-07-15, os estados de robots e termos são apenas
metadados de planejamento e exigem nova verificação antes da publicação. Em
especial, o `202` do EUR-Lex, o WAF do MAECI e o `404` de robots da Gazzetta
Ufficiale permanecem diagnósticos bloqueantes, não permissões nem prova de que
um ato específico existe ou está vigente.

Todas as fontes permanecem `ingestion_enabled=false`, sem corpo armazenado e
com rechecagem live obrigatória. Fonte oficial é referência: a redação pública
deve ser própria, contextualizada para o Brasil e submetida aos gates
jurídico-editoriais, de unicidade, OAB e release.
