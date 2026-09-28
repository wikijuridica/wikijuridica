# Política simplificada de segurança da informação

**Fundamento.** O art. 13 do Regulamento de aplicação da LGPD para Agentes de
Tratamento de Pequeno Porte (Resolução CD/ANPD nº 2, de 27 de janeiro de 2022)
faculta ao agente estabelecer política simplificada de segurança da informação,
que contemple requisitos essenciais e necessários para proteger os dados de
acesso não autorizado e de situações acidentais ou ilícitas de destruição,
perda, alteração ou comunicação indevida. O § 1º manda considerar os custos de
implementação, a estrutura, a escala e o volume das operações; o § 2º diz que a
ANPD considera a existência desta política para os fins do art. 6º, X e do art.
52, § 1º, VIII e IX da LGPD.

**Simplificada, e não vazia.** O art. 12 do mesmo regulamento continua exigindo
medidas administrativas e técnicas essenciais e necessárias. O que a
simplificação dispensa é o aparato formal de uma organização grande — comitês,
matriz de papéis, procedimento de exceção —, não as medidas. Por isso cada item
abaixo aponta **onde a medida está implementada**, com arquivo e linha: uma
política de segurança cujas afirmações não podem ser conferidas no código é uma
promessa, e o art. 12 não se cumpre com promessa.

**Escala considerada.** Operação individual, sem empregados nem operadores
terceiros, com infraestrutura autogerida em servidor próprio. Medido em
2026-09-05: 0 contas cadastradas. As medidas foram escolhidas para serem
corretas nessa escala e continuarem corretas se ela crescer — não para serem
proporcionais a uma operação que não existe.

---

## 1. Autenticação e credenciais

| Medida | Onde |
|---|---|
| Senha guardada apenas como derivação **Argon2id**, com parâmetros validados no boot e chave de 32 bytes exigida — a ausência da chave impede o serviço de abrir as rotas de conta, em vez de deixá-las abrir sem cifra | `internal/contas/conexao.go:66` |
| Chave de cifra (KEK) fora do repositório, em `.env.social` carregado só pela unidade da rede social — o processo do acervo não a recebe | `ops/systemd/wikijuridica-social.service` |
| Cookie de sessão com `Secure`, `HttpOnly` e `SameSite=Lax` — `HttpOnly` tira o cookie do alcance de script, e a escolha de `Lax` em vez de `Strict` está justificada no próprio arquivo | `internal/contas/sessao.go:321-336` |
| Códigos de recuperação de uso único, guardados só como hash — a alternativa seria conta perdida para sempre quando o titular esquecer a senha, já que não há canal de e-mail de saída nesta máquina | `internal/contas` |
| Atraso progressivo em tentativa repetida de entrada, que **nunca bloqueia a conta** — bloquear por tentativa de senha entrega ao atacante uma forma barata de negar o serviço ao titular legítimo | `internal/contas` |

## 2. Dados em repouso

| Medida | Onde |
|---|---|
| Endereço IP do registro de acesso cifrado com **AES-GCM** e indexado por hash, nunca guardado em claro | `internal/lgpd/registrosacesso.go:53-81` |
| Banco da LGPD com `secure_delete(1)`: sem ele, a linha apagada continua legível nas páginas livres do arquivo, e a eliminação do art. 18, VI seria aparente | `internal/lgpd/banco.go:83` |
| Banco da LGPD deliberadamente em `journal_mode=DELETE`, e **não** em WAL: em WAL o efeito do apagamento seguro só se completa no checkpoint. Há teste que mede os bytes do arquivo | `internal/lgpd/banco.go:42-70` |
| Trilha de atendimento do art. 18 chaveada por **pseudônimo**, não pelo identificador da conta | `cmd/social/titular.go` |

**Por que o identificador da conta fica em claro no registro de acesso, e o IP
não.** A assimetria é deliberada e vale a explicação, porque à primeira vista
parece defeito — foi assim que eu mesmo a classifiquei antes de ler o código.

O endereço IP é cifrado porque não precisa ser legível para operar: a guarda do
art. 15 do Marco Civil exige poder apresentá-lo diante de requisição judicial, e
decifrar sob demanda atende isso sem deixá-lo em claro no arquivo. Já o
`conta_id` **precisa** ser legível enquanto a conta existe: é por ele que o
relatório do art. 18, II agrupa os acessos que a própria pessoa vem consultar.
Pseudonimizá-lo na escrita tornaria o direito de acesso inexequível.

E ele não sobrevive à conta. A eliminação do art. 18 o substitui pelo pseudônimo
na mesma operação que apaga o resto — `pseudonimizacoesDoResiduo` inclui
`UPDATE registros_acesso SET conta_id = ?`, e `TestOperacaoDoPlanoApagaOIdDaContaEmRegistrosAcesso`
prova a execução. Independentemente disso, a linha inteira é apagada pelo
varredor ao fim do prazo de retenção.

## 3. Dados em trânsito e superfície pública

| Medida | Onde |
|---|---|
| Todo o tráfego público em HTTPS, por túnel autenticado, sem porta de origem exposta à internet | `ops/` |
| `Content-Security-Policy` com **`script-src 'none'`** em toda a rede social: é a defesa que segura o payload quando a sanitização falhar — e a sanitização é código próprio, logo é código que pode ter defeito | `internal/socialheaders` |
| Resposta que carrega dado de uma pessoa sai com `Cache-Control: no-store` e `X-Robots-Tag: noindex` nos dois canais, sem depender de o middleware acertar | `cmd/social/titular.go:610` |
| Conteúdo enviado por usuário sanitizado por allowlist antes de ser servido | `internal/htmlpolicy` |
| Verificação de origem em toda escrita (CSRF), com token em campo escondido — sem JavaScript | `internal/contas/csrf.go:77` |
| 23 diretivas de limitação de requisição na borda, separando leitura de escrita | `ops/nginx/standalone/nginx.conf` |

## 4. Disponibilidade e recuperação

| Medida | Onde |
|---|---|
| Cópia de segurança dos bancos por `VACUUM INTO`, **nunca** `cp`: com WAL ligado, copiar o `.db` sozinho produz um arquivo que abre e mente, e o erro só aparece quando alguém precisa restaurar | `tools/generate-backup-wiki:122` |
| A cópia falha fechado se o utilitário do SQLite faltar, em vez de degradar para uma cópia silenciosamente inválida | `tools/generate-backup-wiki` |
| `PRAGMA integrity_check` executado **na cópia**, não no original — verificar o original não diz nada sobre o que foi salvo | `tools/generate-backup-wiki:135` |
| O sal de pseudonimização é copiado junto: restaurar o banco sem ele devolveria pseudônimos que não resolvem | `tools/generate-backup-wiki` |
| Vigia de saúde sondando o serviço pelo proxy e pela origem, com detecção de laço de reinício | `tools/check-portal-health` |

## 5. Retenção e descarte

| Medida | Onde |
|---|---|
| Prazo de retenção declarado por finalidade, com marco de contagem — nunca um número solto | `internal/lgpd/finalidades.go` |
| Varredor de retenção que **apaga de verdade**, executado por unidade agendada diária | `cmd/lgpd-expurgo`, `ops/systemd/wikijuridica-lgpd-expurgo.timer` |
| Registro das operações de tratamento **gerado a partir da mesma tabela** que o varredor lê — documento e comportamento com uma fonte só | `cmd/generate-registro-de-tratamento` |

## 6. Incidentes

Não há equipe de plantão, e dizer o contrário seria descrever uma organização que
não existe. O que existe:

- **Detecção**: o vigia de saúde roda por agendamento e alerta em falha; o
  ledger de acesso da origem grava cada requisição com identificação de agente,
  estado e classificação de rota.
- **Contenção**: a chave de cifra é única e substituível; o serviço da rede
  social é isolado do acervo, de modo que a contenção de um não derruba o outro.
- **Comunicação**: incidente que possa acarretar risco ou dano relevante é
  comunicado à ANPD e ao titular na forma da Resolução CD/ANPD nº 15, de 24 de
  abril de 2024, pelo canal publicado na página de privacidade. O art. 14, II da
  Res. 2/2022 concede prazo em dobro ao agente de pequeno porte, **exceto**
  quando houver potencial comprometimento à integridade física ou moral dos
  titulares.

## 7. O que esta política não cobre

- **Segurança física do servidor**, que segue o regime do provedor de
  hospedagem.
- **O dispositivo do titular**: senha reutilizada, navegador comprometido ou
  sessão deixada aberta em computador alheio estão fora do alcance de qualquer
  medida do lado do servidor.
- **Conteúdo que o próprio titular publica**: a plataforma o sanitiza e o
  modera, mas não pode desfazer a divulgação de um dado que a pessoa escolheu
  tornar público.

---

**Revisão.** Esta política é revista quando o enquadramento como agente de
pequeno porte for reavaliado na forma da seção 6 de
`ENQUADRAMENTO_PEQUENO_PORTE.md`, e sempre que uma medida acima deixar de
descrever o código — hipótese em que a correção é do documento **ou** do código,
nunca a de deixar os dois divergindo em silêncio.
