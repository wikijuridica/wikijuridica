# Registro das operações de tratamento de dados pessoais

**Documento gerado — não edite à mão.** Ele é emitido por
`./tools/go-modern run ./cmd/generate-registro-de-tratamento` a partir de
`internal/lgpd.Finalidades()`, que é a mesma tabela que o varredor de retenção
lê para apagar e que o executor do art. 18 consulta para montar o plano de
eliminação. Editar este arquivo faria o documento divergir do comportamento —
que é exatamente o defeito que gerá-lo existe para impedir.

- **Emitido em:** 2026-09-05
- **Controlador:** Rafael Toledo da Silva Duarte
- **Canal de atendimento ao titular:** rafaeltoledoadvogado@outlook.com
- **Regime declarado:** Agente de pequeno porte (Res. CD/ANPD 2/2022, art. 2º, I); canal do art. 11, §1º
- **Versão da tabela de finalidades:** 1

## Fundamento e alcance

O art. 37 da Lei 13.709/2018 obriga o controlador a manter registro das
operações de tratamento que realizar. O art. 9º do Regulamento de aplicação da
LGPD para Agentes de Tratamento de Pequeno Porte (Resolução CD/ANPD nº 2, de
27 de janeiro de 2022) permite cumpri-la **de forma simplificada**.

Simplificada é a forma, nunca o conteúdo: o art. 6º do mesmo regulamento diz
que a dispensa ou flexibilização não isenta do cumprimento dos demais
dispositivos da LGPD, inclusive das bases legais e dos princípios. Por isso
cada linha abaixo declara base legal, prazo de retenção com o marco de
contagem, o que o titular pode eliminar e **qual código executa o
tratamento** — este último para que a afirmação seja conferível, e não
apenas declarada.

## As operações

### Medição de audiência das páginas públicas

- **Identificador interno:** `analytics`
- **Base legal:** art. 7º, IX da Lei 13.709/2018 (legítimo interesse), com direito de oposição
- **Retenção:** 14 meses a contar da coleta
- **O titular pode eliminar:** sim, integralmente
  - Sim, e a oposição pode ser exercida a qualquer momento, no próprio navegador.
- **Executado por:** `internal/webanalytics.Loader`

### Conta e credenciais de acesso

- **Identificador interno:** `conta`
- **Base legal:** art. 7º, V (execução de contrato) da Lei 13.709/2018
- **Retenção:** 30 dias após o encerramento da conta
- **O titular pode eliminar:** parcialmente
  - Sim, exceto o resíduo legal do art. 16, que permanece pseudonimizado.
- **Executado por:** `internal/contas.Cadastrar`

### Conteúdo publicado pelo usuário

- **Identificador interno:** `conteudo_publico`
- **Base legal:** art. 7º, V e IX da Lei 13.709/2018
- **Retenção:** enquanto o conteúdo estiver publicado
- **O titular pode eliminar:** parcialmente
  - A autoria sai sempre; o texto segue a opção escolhida pelo titular entre as três do art. 18.
- **Executado por:** `internal/socialconteudo.CriarDuvida`

### Relato do caso e documentos enviados

- **Identificador interno:** `intake_de_caso`
- **Base legal:** art. 7º, V e VI da Lei 13.709/2018
- **Fundamento para dado sensível (art. 11):** art. 11, II, "d" da Lei 13.709/2018 (exercício regular de direitos em processo)
- **Retenção:** 5 anos após o encerramento do caso
  - **Exceção (sem_contratacao):** 90 dias
- **O titular pode eliminar:** parcialmente
  - Sim, quando não houver contratação; havendo, prevalece a guarda profissional.
- **Executado por:** ainda não há código — pendente: o compartimento de sigilo nasce em F3

### Mensagens entre usuário e advogado

- **Identificador interno:** `mensageria`
- **Base legal:** art. 7º, V da Lei 13.709/2018 e sigilo profissional do art. 34 do EOAB
- **Retenção:** igual à do caso a que a conversa pertence
- **O titular pode eliminar:** sim, integralmente
  - Sim, respeitada a guarda do caso quando houver contratação.
- **Executado por:** ainda não há código — pendente: a mensageria nativa nasce em F3

### Trilha de moderação e decisões sobre conteúdo

- **Identificador interno:** `moderacao`
- **Base legal:** art. 7º, II da Lei 13.709/2018 — os Temas 987 e 533 do STF impõem a trilha
- **Retenção:** 5 anos a contar do registro
- **O titular pode eliminar:** não — a retenção decorre de obrigação legal ou regulatória
  - Não: a guarda é obrigação legal, e o art. 16, I ressalva expressamente essa hipótese.
- **Executado por:** `internal/moderacao.Decidir`

### Atuação processual e ato público

- **Identificador interno:** `processual`
- **Base legal:** art. 7º, II e VI da Lei 13.709/2018 (ato público e exercício de direitos)
- **Retenção:** enquanto a inscrição na OAB estiver ativa, e por 5 anos depois
- **O titular pode eliminar:** não — a retenção decorre de obrigação legal ou regulatória
  - Ato processual é público por determinação legal; a eliminação a pedido não o alcança.
- **Executado por:** ainda não há código — pendente: a superfície processual nasce em F4

### Registros de acesso à aplicação

- **Identificador interno:** `seguranca`
- **Base legal:** art. 7º, IX da Lei 13.709/2018 (legítimo interesse), com o prazo do art. 15 da Lei 12.965/2014 adotado como padrão próprio
- **Retenção:** 6 meses, prazo adotado pelo parâmetro do art. 15 do Marco Civil da Internet
- **O titular pode eliminar:** não — a retenção decorre de obrigação legal ou regulatória
  - Não durante os 6 meses de guarda; depois deles o expurgo é automático.
- **Executado por:** `internal/lgpd.RegistraAcesso`

### Verificação da inscrição na OAB

- **Identificador interno:** `verificacao_oab`
- **Base legal:** art. 7º, V (execução de contrato) da Lei 13.709/2018
- **Retenção:** a evidência é apagada 30 dias após a decisão; permanece apenas o sha256 dela
- **O titular pode eliminar:** não — a retenção decorre de obrigação legal ou regulatória
  - Não: o sha256 da evidência sustenta o selo perante terceiros e não é dado identificável isolado.
- **Executado por:** `internal/verificacaooab.Pedir`

## O que este registro não cobre

Dizer o alcance é parte do registro: um documento que se apresenta como
completo sem ser é pior para o titular do que um que declara a própria borda.

- **Operações que ainda não existem** aparecem acima com o substrato marcado.
  Elas estão na tabela porque a finalidade foi decidida antes do código, e
  apagá-las daqui até o código nascer esconderia a intenção de tratar.
- **Registro de acesso do servidor web** (endereço IP e rota), mantido sob o
  prazo do art. 15 do Marco Civil da Internet, aparece sob a finalidade de
  segurança e é apagado pelo varredor ao fim do prazo.
- **Conteúdo publicado por terceiros** nas mesmas conversas pertence a eles e
  é tratado sob a finalidade de conteúdo público, não sob a conta de quem o lê.

## Como conferir este documento

```
./tools/go-modern run ./cmd/generate-registro-de-tratamento
git diff docs/politica/REGISTRO_DE_TRATAMENTO.md
```

Diferença vazia significa que o documento descreve o código de hoje. Diferença
não vazia é o próprio aviso de que o sistema mudou e o registro precisa ser
reemitido — e a data de emissão acima é a que vale perante a autoridade.
