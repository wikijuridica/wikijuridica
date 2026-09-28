# Registro de enquadramento como agente de tratamento de pequeno porte

> **Minuta para revisão e assinatura do controlador.** Enquanto não estiver
> datada e assinada, este documento é a proposta técnica de enquadramento, não a
> declaração do agente. A engenharia que ele descreve já está implementada; o
> que falta é o ato de quem responde.

**Finalidade deste documento.** O art. 5º do Regulamento de aplicação da LGPD
para Agentes de Tratamento de Pequeno Porte (Resolução CD/ANPD nº 2, de 27 de
janeiro de 2022) determina que o agente comprove o enquadramento **em até quinze
dias** quando a ANPD solicitar. Quinze dias não é prazo para produzir a análise —
é prazo para entregá-la. Este registro existe para que a resposta esteja pronta
antes da pergunta, com os números que a sustentam medidos e datados.

---

## 1. Identificação do agente de tratamento

| | |
|---|---|
| **Controlador** | Rafael Toledo da Silva Duarte |
| **Natureza** | Pessoa natural |
| **Inscrição profissional** | OAB/RJ 227.191 — conferível no Cadastro Nacional dos Advogados |
| **Canal de atendimento ao titular** | rafaeltoledoadvogado@outlook.com |
| **Aplicação** | Rede social jurídica em `https://wikijuridica.com.br/redesocial/` |
| **Operador** | Não há. A infraestrutura é própria e autogerida; não há terceiro tratando dados por conta do controlador. |

Os três primeiros campos e o canal saem de `content/site.json`, que é a fonte
única da identidade editorial deste projeto — nenhum deles é escrito em código,
e o teste `TestEditorialIdentityComesFromSiteConfigNotRuntimeHardcode` reprova a
tentativa.

## 2. O enquadramento, e o dispositivo que o autoriza

O art. 2º, I do Regulamento define agentes de tratamento de pequeno porte como
"microempresas, empresas de pequeno porte, startups, pessoas jurídicas de
direito privado, inclusive sem fins lucrativos, nos termos da legislação
vigente, bem como **pessoas naturais** e entes privados despersonalizados que
realizam tratamento de dados pessoais, assumindo obrigações típicas de
controlador".

O controlador é pessoa natural que realiza tratamento assumindo obrigações
típicas de controlador. O enquadramento decorre diretamente do inciso, sem
necessidade de equiparação.

## 3. As três exclusões do art. 3º, examinadas uma a uma

O art. 3º afasta do tratamento jurídico diferenciado quem se enquadre em
qualquer de três hipóteses. Nenhuma delas se verifica, e o motivo de cada uma
está abaixo com o fato que a sustenta.

### 3.1. Inciso I — tratamento de alto risco

O art. 4º considera de alto risco o tratamento que atenda **cumulativamente** a
pelo menos um critério geral **e** um critério específico. A conjunção é
decisiva: um critério específico isolado não caracteriza alto risco.

**Critérios gerais — nenhum se verifica hoje, e a medição é reprodutível.**

| Critério geral | Medido em 2026-09-05 | Verifica-se? |
|---|---|---|
| (a) tratamento em larga escala | **0 contas**, 0 perfis, 0 dúvidas, 0 respostas em `var/social/social.db`; **0 registros de acesso** em `var/social/lgpd.db`; **1 visitante distinto** medido na superfície social pelo log de origem | **Não** |
| (b) tratamento que possa afetar significativamente interesses e direitos fundamentais | O serviço é informativo e gratuito; não condiciona acesso a direito, não concede nem nega benefício, não pontua nem classifica pessoas. A moderação alcança conteúdo publicado, e não a fruição do serviço por quem o lê | **Não** |

O § 1º do art. 4º caracteriza larga escala pelo "número significativo de
titulares, considerando-se, ainda, o volume de dados envolvidos, bem como a
duração, a frequência e a extensão geográfica do tratamento". Com zero titulares
cadastrados, nenhum desses fatores tem sobre o que incidir.

**Critérios específicos — dois merecem exame honesto, e é por isso que a seção 5
existe.**

| Critério específico | Situação | Verifica-se? |
|---|---|---|
| (a) tecnologias emergentes ou inovadoras | Não há decisão automatizada sobre pessoas. A plataforma serve HTML estático e dinâmico, sem inferência sobre titulares | Não |
| (b) vigilância ou controle de zonas acessíveis ao público | Não há | Não |
| (c) decisões unicamente automatizadas, inclusive de perfil | Não há. Nenhuma decisão sobre pessoa é tomada sem intervenção humana; a moderação registra decisão humana com trilha, e a reputação **não é exibida publicamente nem ordena qualquer listagem** | Não |
| (d) dados sensíveis, de crianças, adolescentes ou idosos | **Possível, e declarado.** Conteúdo jurídico pode conter dado de saúde, filiação ou situação familiar quando o próprio titular o escreve. Hoje não há conteúdo publicado por terceiro | Potencialmente, no futuro |

**Conclusão do inciso I.** Ainda que o critério específico (d) venha a se
verificar, ele **não basta**: sem critério geral concomitante não há alto risco
na definição do art. 4º. O enquadramento se sustenta hoje pela ausência dos dois
critérios gerais, que é a metade medida da conjunção.

### 3.2. Inciso II — receita bruta acima do limite

A aplicação não aufere receita. Não há cobrança de usuário, assinatura,
publicidade, patrocínio ou intermediação remunerada. A receita profissional do
controlador decorre do exercício da advocacia, atividade distinta da operação
desta aplicação e sujeita a regime próprio.

### 3.3. Inciso III — grupo econômico

Não há grupo econômico de fato ou de direito. O controlador é pessoa natural e a
infraestrutura é individual.

## 4. As flexibilizações adotadas, com o que cada uma exigiu de engenharia

O art. 6º é explícito: a dispensa ou flexibilização **não isenta** do
cumprimento dos demais dispositivos da LGPD, inclusive das bases legais e dos
princípios. Cada item abaixo diz o que foi flexibilizado **e o que se cumpriu no
lugar** — porque flexibilização sem contrapartida implementada é dispensa que
ninguém concedeu.

| Art. | O que o regulamento faculta | O que esta aplicação faz |
|---|---|---|
| **7º** | informações e requisições do titular por meio eletrônico | As requisições do art. 18 são atendidas por rota autenticada no próprio site (acesso, correção, eliminação e portabilidade), com trilha datada de cada atendimento — mais forte que e-mail para provar o atendimento |
| **9º** | registro simplificado das operações (art. 37 da LGPD) | `docs/politica/REGISTRO_DE_TRATAMENTO.md`, **gerado** a partir de `internal/lgpd.Finalidades()` — a mesma tabela que o varredor de retenção lê para apagar. Documento e comportamento têm uma fonte só |
| **11** | dispensa de indicar encarregado | **Adotada.** O canal do § 1º está publicado e é o mesmo da seção 1. Ver a seção 5 |
| **13** | política simplificada de segurança da informação | `docs/politica/POLITICA_SIMPLIFICADA_DE_SEGURANCA.md`, descrevendo as medidas que já operam |
| **14** | prazo em dobro no atendimento ao titular, na comunicação de incidente e nas declarações | **Não invocado por padrão.** O atendimento das rotas do art. 18 é imediato, por construção — a dilação existe se necessária, mas usá-la quando o sistema responde na hora seria invocar prazo sem precisar dele |
| **15** | declaração simplificada do art. 19, I em até quinze dias | O relatório de acesso é emitido no ato, pela rota autenticada |

## 5. O encarregado: por que não há designação, e o que a substitui

O art. 11 do Regulamento dispensa o agente de pequeno porte de indicar
encarregado, e o § 1º mantém de pé o dever de **disponibilizar canal de
comunicação com o titular** para atender o art. 41, § 2º, I da LGPD. O canal está
publicado na página de privacidade, na página de transparência e na seção 1 deste
documento.

**A dispensa é a escolha certa aqui, e não a escolha cômoda.** O art. 19, § 1º,
II da Resolução CD/ANPD nº 18, de 16 de julho de 2024, arrola como hipótese de
conflito de interesse "o acúmulo das atividades de encarregado com outras que
envolvam a tomada de decisões estratégicas sobre o tratamento de dados pessoais
pelo controlador". Com um responsável único, designá-lo encarregado colocaria a
mesma pessoa decidindo o tratamento e fiscalizando a própria decisão.

**Três ressalvas que a leitura honesta da norma impõe, e que registro para que
esta seção não seja lida como mais protetora do que é:**

1. O § 2º do mesmo art. 19 diz que a existência de conflito "será objeto de
   **verificação no caso concreto**". A presunção é relativa, não absoluta.
2. O art. 21, parágrafo único, II admite "implementar medidas para afastar o
   risco de conflito de interesse" como alternativa a não indicar. Designar com
   mitigação documentada era, portanto, caminho igualmente lícito.
3. O art. 11, § 2º da Res. 2/2022 considera a indicação voluntária **política de
   boas práticas e governança** para o art. 52, § 1º, IX da LGPD — o que a ANPD
   pondera na dosimetria de eventual sanção.

Escolheu-se a dispensa por ela ser a que descreve a realidade sem construir uma
ficção: não há estrutura interna a quem delegar, e anunciar um encarregado que é
o próprio controlador daria ao titular uma garantia de independência que não
existiria. Se o enquadramento mudar na forma da seção 6, a designação com
mitigação passa a ser o caminho, e este documento é revisto antes disso.

## 6. Quando este enquadramento deixa de valer — e como se descobre

Declaração de enquadramento que ninguém revisita é declaração que envelhece em
silêncio, e o art. 5º cobra a comprovação **no dia em que a ANPD perguntar**, não
no dia em que ela foi escrita.

**O gatilho é medido, não lembrado.** `tools/check-enquadramento-pequeno-porte`
lê o número real de titulares no banco e reprova quando a operação se aproxima do
que caracterizaria larga escala, obrigando a reavaliação enquanto ainda há tempo
de fazê-la. Ele roda na suíte de qualidade e é a razão de este documento ter data
de emissão.

Reavalia-se o enquadramento, com registro datado, quando ocorrer qualquer de:

- **o número de titulares cadastrados cruzar o limiar** que o gate vigia, ou o
  volume, a duração, a frequência ou a extensão geográfica do tratamento
  passarem a caracterizar larga escala na forma do art. 4º, § 1º;
- **o serviço passar a condicionar o exercício de um direito ou a fruição de um
  serviço** ao tratamento — hipótese do art. 4º, § 2º;
- **passar a existir decisão unicamente automatizada** sobre pessoas, inclusive
  de perfilamento;
- **a aplicação passar a auferir receita** que se aproxime dos limites do art.
  3º, II, ou o controlador integrar grupo econômico.

Verificada qualquer delas em conjunto com um critério específico do art. 4º, II,
o tratamento passa a ser de alto risco, o regime diferenciado cessa (art. 3º, I),
e voltam a ser exigíveis, entre outras, a indicação de encarregado por ato formal
na forma do art. 3º da Res. 18/2024 e o registro de operações na forma plena do
art. 37 da LGPD.

## 7. Fontes normativas

Todas conferidas no texto oficial em 2026-09-05, e não em resumo de terceiro:

- **Lei nº 13.709, de 14 de agosto de 2018** (LGPD) — arts. 5º, VI e VIII; 18; 19;
  37; 41 e §§; 52, § 1º.
- **Resolução CD/ANPD nº 2, de 27 de janeiro de 2022** — Regulamento de aplicação
  da LGPD para Agentes de Tratamento de Pequeno Porte, arts. 2º a 16.
- **Resolução CD/ANPD nº 18, de 16 de julho de 2024** — Regulamento sobre a
  atuação do encarregado, arts. 3º, 8º, 9º, 15, 18 a 21.
- **Lei nº 12.965, de 23 de abril de 2014** (Marco Civil da Internet) — art. 15,
  quanto à guarda de registro de acesso a aplicação.

---

## Declaração do controlador

Declaro, para os fins do art. 5º do Regulamento aprovado pela Resolução CD/ANPD
nº 2, de 27 de janeiro de 2022, que a aplicação identificada na seção 1 se
enquadra como agente de tratamento de pequeno porte, pelas razões e com os fatos
registrados nas seções 2 e 3, e que adotei as flexibilizações da seção 4 com as
contrapartidas ali descritas.

Comprometo-me a reavaliar este enquadramento na ocorrência de qualquer das
hipóteses da seção 6, com novo registro datado.

<br>

Local e data: ________________________________________

<br>

Assinatura: __________________________________________

Rafael Toledo da Silva Duarte — OAB/RJ 227.191
