# Achados de vigência e de citação inventada — 2026-08-07

Registro durável de três achados que custaram pesquisa real (corpus local, API
pública e fonte oficial primária) e que existiam apenas no contexto de uma
sessão. Cada um nomeia o dispositivo, a fonte conferida e a página afetada.

## 1. RN ANS 259/2011 está REVOGADA — 6 citações no ar afirmam o contrário

A Resolução Normativa ANS nº 259/2011 (prazos máximos de atendimento) foi
revogada expressamente pela **RN ANS nº 566/2022, art. 16, I**, com vigência a
partir de 1º de fevereiro de 2023:

> "Art. 16. Ficam revogados: I - a Resolução Normativa – nº 259, de 17 de junho
> de 2011; ... Art. 17. Esta Resolução Normativa entra em vigor em 1 de
> fevereiro de 2023."

Fonte conferida (HTTP 200 em 2026-08-07):
`https://www.ans.gov.br/component/legislacao/?view=legislacao&task=TextoLei&format=raw&id=NDM0MQ%3D%3D`

Norma vigente hoje: **RN 566/2022**, alterada pontualmente pela RN 665/2026
(26/02/2026) só no §2º do art. 1º (definição de "região de saúde"). Prazos
(art. 3º), indisponibilidade (art. 4º), inexistência (art. 5º) e reembolso
integral em 30 dias (art. 10) seguem intactos.

**Páginas afetadas, todas publicadas:** `data/editorial/v2_pages/saude-02.jsonl`
(3 ocorrências), `saude-03.jsonl` (1), `saude-09.jsonl` (2). Uma delas afirma
literalmente que a RN 259/2011 "está em vigor" — afirmação falsa sobre norma
revogada há três anos.

**Armadilha documentada:** a própria página de consumo da ANS em
`gov.br/ans/.../prazos-maximos-de-atendimento` **ainda atribui os prazos à RN
259/2011**. Quem conferir por ali confirma o erro. A âncora correta é o texto
legal da RN 566/2022, não a página de orientação.

## 2. `cid-italiana-por-casamento` afirma instituto jurídico INVENTADO

A página (ainda **não publicada**, em `data/editorial/v2_blocked_drafts/cidadania-04.jsonl`) afirma:

> "A legislação italiana também prevê a revogação da cidadania concedida por
> casamento, dentro de prazo determinado após a naturalização, quando se
> comprova em processo penal definitivo que o vínculo era simulado para obter o
> benefício migratório — o chamado matrimônio de conveniência."

O dispositivo real de revogação é o **art. 10-bis da Legge 91/1992**, e ele
cobre **exclusivamente condenação definitiva por crimes de terrorismo** (art.
407, co. 2, lett. a, n. 4 do CPP italiano e arts. 270-ter e 270-quinquies.2 do
Código Penal italiano). **Não existe** na Legge 91/1992 revogação por casamento
simulado. A afirmação é fabricada e viola a proibição de inventar dispositivo.

**Ação obrigatória:** corrigir ou remover a frase ANTES de promover a página.

Nota correlata: o requisito de italiano nível B1 foi inserido pelo DL 113/2018
no **art. 9.1** da Legge 91/1992, não no art. 5º. O art. 5º trata só de prazo de
residência (2 anos na Itália / 3 no exterior, metade com filho comum) e da
persistência do vínculo conjugal. Ancorar o B1 no art. 5º é citação mal
atribuída.

Fonte: `https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:legge:1992-02-05;91`
(HTTP 200; o HTML devolve `eli:version_date` = 2026-08-07, texto consolidado
vigente).

## 3. `sfb-reembolso-bariatrica-fora-rede-falta-credenciado` mistura dois regimes

A página (ainda **não publicada**, em `v2_blocked_drafts/saude-w3-03.jsonl`) abre
com um cenário de **inexistência** de prestador ("o único hospital credenciado
fica a 300 quilômetros"), que é regido pelo **art. 5º da RN 566/2022**
(municípios limítrofes / região de saúde), mas aplica na seção seguinte o regime
do **art. 4º** (indisponibilidade — quando existe prestador no município e ele
não atende no prazo), oferecendo "atendimento por prestador particular no mesmo
município". Se não há credenciado no município, o art. 4º não é o aplicável e o
art. 5º não prevê essa opção.

A página irmã (`sfb-reembolso-psicoterapia-fora-rede-deficit-de-rede`) faz a
distinção corretamente ("indisponibilidade não é sinônimo de inexistência"), o
que confirma tratar-se de defeito de redação e não de leitura equivocada.

Secundário: a página funda o reembolso só na Lei 9.656/1998, art. 12, e ignora o
**art. 10 da RN 566/2022** (reembolso integral em até 30 dias por descumprimento
dos arts. 4º, 5º ou 6º), que é o fundamento mais forte disponível.

## 4. Fontes oficiais localizadas para hints que travavam 30 páginas

- **Seguro habitacional / MIP:** a norma específica vigente é a **Resolução CNSP
  nº 447, de 10/10/2022**, que revogou as Resoluções CNSP 205/2009 e 212/2010
  (art. 42). PDF oficial (HTTP 200):
  `https://www2.susep.gov.br/safe/scripts/bnweb/bnmapi.exe?router=upload%2F26564`
  — o link equivalente em gov.br/susep devolve 404. Competência normativa é do
  CNSP; a SUSEP fiscaliza e publica (Decreto-Lei 73/1966). A Circular SUSEP
  621/2021, cogitada antes, é de **seguros de danos** e não sustenta cobertura
  de morte/invalidez.
- **RN 566/2022:** a chave `ans-rn-566-2022-garantia-atendimento` **já existe**
  no catálogo. O hint do portfólio foi normalizado para ela em
  `source_hints_worktree_20260804` e depois **revertido** para o texto livre
  "RN 259/2011 (ANS)" — é regressão de normalização, não ausência de catálogo.
- **Legge 91/1992:** a normalização anterior mapeou este hint para
  `cc-2002-art-5` — o **art. 5º do Código Civil brasileiro** (maioridade civil).
  Mapeamento gravemente errado, a corrigir com duas chaves específicas (art. 5º
  para prazo/vínculo; art. 9.1 para o requisito de idioma B1).
