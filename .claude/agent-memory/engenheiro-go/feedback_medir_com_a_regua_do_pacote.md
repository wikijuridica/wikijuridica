---
name: feedback-medir-com-a-regua-do-pacote
description: Medição sobre corpus real vai num _test.go do pacote DONO da régua, gated por env de snapshot datado, e todo "zero" exige controle positivo na mesma população
metadata:
  type: feedback
---

Quando a pergunta é "quantos registros do corpus o critério X aprova", a medição mora num
`_test.go` **dentro do pacote que implementa X**, gated por variável de ambiente que aponta um
**snapshot datado** do corpus — nunca num `cmd/` novo, nunca em Python.

**Why:** as réguas deste repo (`elegivel`, `procedimental`, `dispositivosSubstantivos`,
`admissibilidade`) são **não exportadas**. Medir de fora obriga a copiá-las, e cópia de régua é o
defeito que o §1.20f do plano registra: dois agentes mediram a mesma pergunta e devolveram 2.477
contra 1.225. O maestro é explícito: *"o binário é a autoridade, não replicação em Python — nesta
sessão uma replicação minha bateu com o esperado e estava 5,3× errada."* E o corpus é appendado pelo
coletor durante a passada: número contra dado em movimento não é reproduzível.

**How to apply:**

1. Arquivo novo ao lado (`medicao_<frente>_test.go`), `package main` do próprio comando. Arquivo
   NOVO não sofre lost update mesmo com outra frente editando o `main.go` — mas confira colisão de
   nome (`relata` já existia; prefixe tudo).
2. `t.Skipf` barulhento quando a env não está definida, dizendo qual é e por quê. Rode com
   `-run '^TestMede'` — o pacote pode ter testes alheios quebrados no momento.
3. Grave no relatório o **sha256 do arquivo da régua** junto dos números. Se ela está sob edição de
   outra frente, isso é o que torna a reexecução comparável depois do commit dela.
4. **Todo "zero" exige controle positivo NA MESMA população.** Em 2026-09-16 a medição devolveu
   "322 de 322 sem citação ambígua"; o contador de ambiguidade tinha disparado **zero** vezes nos 790
   registros — indistinguível de contador morto. Ampliado o controle ao grupo inteiro (24.571), ele
   disparou 32 vezes, e só aí o zero virou medição.
5. **Piso de volume antes do veredito.** Taxa sobre dezenas de casos não reprova detector: reprovar
   por N pequeno manda calibrar contra dado que não existe. `AgRg no HC` deu N=0 (as turmas criminais
   nunca foram coletadas) — o resultado honesto é "não medido", não "reprovado".

6. **Rode a bancada do próprio instrumento ANTES de mexer nele — ela pode estar vermelha há dias.**
   Em 2026-09-16 `tools/test_check_jsonld_cobertura.py` reprovava 6 de 11 desde que um tipo novo
   entrou no gate sem a fixture acompanhar. Sem medir esse baseline eu teria atribuído os vermelhos
   à minha mudança (ou, pior, lido "verde depois" como prova). O baseline é a primeira medição, não
   a última.
7. **O controle positivo é sobre a FORMA REAL do artefato, não sobre a forma que o código supõe.**
   Um marcador que monta `'"' + path + fragmento + '"'` supondo `@id` relativo nunca casa contra um
   `@id` absoluto — e "presente=0" num detector novo é indistinguível de "nunca casou". Ancore na
   CHAVE do campo (`"@id":"`), nunca só no delimitador: a aspa sozinha casa a mesma URL sob outra
   chave. Fixture que passa por um caminho que o dado vivo não percorre (campo opcional não
   preenchido) é verde por outro motivo — preencha-o com o valor que a produção grava.

Ver [[project-p3-produtores-orfaos]] e [[feedback-parar-em-arquivo-concorrente]].
