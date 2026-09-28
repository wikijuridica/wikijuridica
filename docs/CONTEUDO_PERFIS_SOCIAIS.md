# Conteúdo dos perfis oficiais

Textos prontos para colar. O login nas plataformas é a única parte que depende
do titular; a redação está aqui para que a ação se reduza a copiar e publicar.

Perfis declarados em `content/site.json` — a forma das URLs é a que responde 200,
e mudar a barra final cria uma segunda identidade para o mesmo perfil:

| Plataforma | URL | Entidade |
|---|---|---|
| Instagram | `https://www.instagram.com/wiki.juridica/` | marca Wiki Jurídica |
| Facebook | `https://www.facebook.com/wikijuridica` | marca Wiki Jurídica |
| LinkedIn | `https://www.linkedin.com/in/rafaeltoledoadvogado` | Rafael Toledo (pessoa) |

---

## 1. Bio — e por que ela precisa mudar

**A bio atual do Instagram tem três problemas**, medidos em 2026-08-27:

1. **Erro de ortografia:** diz *"Palataforma"* no lugar de "Plataforma". Um
   portal cujo contrato editorial trata acento faltando como falha P0 mandaria o
   visitante de `/sobre/` para uma bio com erro de digitação.
2. **Declara-se inacabado:** *"em Construção"*, com 10.107 páginas no ar. A
   frase contradiz o acervo e desfaz a confiança que a página institucional
   acabou de construir.
3. **Não identifica o responsável técnico.** Esta é a exigência formal: o
   Provimento OAB 205/2021, art. 3º, §1º, remete ao art. 44, §1º do Código de
   Ética (Res. CFOAB 02/2015), pelo qual o advogado **fará constar seu nome e o
   número de inscrição na OAB** na publicidade profissional. E o art. 1º, §1º do
   mesmo provimento atribui a responsabilidade pelo conteúdo do perfil à pessoa
   física identificada — que responde por ele perante a Ordem.

### Instagram e Facebook (perfis da marca)

```
Wiki Jurídica — direito brasileiro explicado com fonte oficial.
Responsável técnico: Rafael Toledo — OAB/RJ 227191.
Conteúdo informativo; não substitui consulta jurídica.
wikijuridica.com.br
```

Se o limite de caracteres apertar (o Instagram permite 150), a linha que **não**
pode cair é a da inscrição na OAB — ela é exigência, não estilo:

```
Direito brasileiro explicado com fonte oficial.
Responsável técnico: Rafael Toledo — OAB/RJ 227191.
wikijuridica.com.br
```

### LinkedIn (perfil da pessoa)

O perfil é pessoal e já identifica o titular; o que falta é o vínculo recíproco
com o portal, que é o que fecha o `sameAs`. Na seção "Sobre":

```
Advogado inscrito na OAB/RJ sob o nº 227191. Responsável técnico do portal
Wiki Jurídica (wikijuridica.com.br), um acervo de conteúdo jurídico informativo
produzido a partir de fontes oficiais, com revisão profissional e política de
fontes pública.
```

### Link recíproco — por que importa

`sameAs` declara ao buscador que o portal e o perfil são a mesma entidade. A
confirmação vem de o **outro lado apontar de volta**: o Instagram já tem o link
na bio; o Facebook e o LinkedIn precisam do endereço `wikijuridica.com.br` no
campo de site. Sem reciprocidade, a declaração fica unilateral e vale menos.

---

## 2. Peças de estreia

Cinco peças, uma por área, todas derivadas de páginas **reais** do acervo — nada
aqui é inventado, e cada afirmação está sustentada pela fonte oficial que a
página já registra em `source_provenance`.

**A escolha das cinco não foi por apelo**, foi por estabilidade da norma: o
acervo tem 6.841 páginas com FAQ e título curto, mas post em rede social **não
se corrige depois de publicado** como página se corrige. As selecionadas se
apoiam em CDC (1990), Código Civil (2002) e regulação setorial consolidada —
nenhuma depende de norma em trânsito. (Foram descartadas, por esse critério,
peças boas sobre o Estatuto dos Direitos do Paciente, de abril de 2026, e sobre
o DPVAT, cuja LC 207/2024 foi revogada pela LC 211/2024 antes de vigorar.)

**Limites que valem para todas** (Provimento 205/2021, arts. 2º, 3º e 7º):
informar, nunca prometer resultado; sem preço, sem "consulte-nos", sem verbo de
contratação; sem caso concreto de cliente; sem sensacionalizar tragédia.

---

### Peça 1 · Família

> **Quem fica com o cachorro depois da separação?**
>
> A lei brasileira ainda trata o animal como bem (Código Civil, art. 1.228), mas
> a prática dos tribunais foi além disso: o que se discute hoje é quem tem
> melhores condições de cuidar, e não apenas quem pagou pelo animal.
>
> Não existe "pensão" para animal de estimação no sentido do direito de família.
> O que se admite é a fixação, por acordo ou decisão, de uma contribuição para
> custear despesas — com natureza de obrigação civil comum.
>
> Como funciona, com a fonte oficial: wikijuridica.com.br/familia/guarda-animal-estimacao/

### Peça 2 · Consumidor / Saúde

> **Assinou o plano de saúde e se arrependeu? O prazo existe — e não começa quando você imagina.**
>
> O art. 49 do Código de Defesa do Consumidor dá sete dias para desistir de
> contratação feita fora do estabelecimento. Na contratação eletrônica de plano
> de saúde, regulada pela RN 413/2016 da ANS, esse prazo corre a partir da
> **vigência** do contrato — que, em regra, se inicia com o pagamento efetivo da
> primeira mensalidade.
>
> A diferença entre contar da assinatura e contar da vigência decide se o pedido
> ainda está no prazo.
>
> O que a norma diz: wikijuridica.com.br/saude/direito-de-arrependimento-plano/

### Peça 3 · Bancário

> **Saques que você não reconhece no cartão consignado**
>
> Contestar a operação é o primeiro passo — mas há um segundo, que costuma ser
> esquecido: pedir que o nome não seja negativado enquanto a contestação corre.
>
> A inscrição em cadastro de inadimplentes por dívida formalmente contestada é
> frequentemente questionada em juízo. Se a negativação já ocorreu, o pedido de
> retirada precisa ser feito junto com a contestação, e não depois.
>
> Passo a passo e base legal: wikijuridica.com.br/bancario/cartao-consignado-saques-nao-reconhecidos-pelo-titular/

### Peça 4 · Aéreo / Acessibilidade

> **Cadeira de rodas danificada no voo: o que a companhia deve fazer**
>
> A obrigação não começa no pedido de indenização. Pela Resolução ANAC 280/2013,
> a empresa deve fornecer um substituto equivalente **já no desembarque** — a
> indenização é etapa posterior, após a constatação regulamentar de perda ou
> inutilização.
>
> Saber a ordem das duas coisas evita aceitar só a segunda.
>
> O que exigir, com a norma: wikijuridica.com.br/aereo/cadeira-rodas-danificada-indenizacao/

### Peça 5 · Consumidor / Viagem

> **A agência não avisou que o visto era obrigatório. Ela responde?**
>
> Não automaticamente — e essa é a parte que costuma surpreender. É preciso
> examinar o serviço efetivamente contratado, a informação que estava
> disponível, a orientação prestada, a regra vigente à época e a conduta do
> próprio viajante.
>
> O dever de informar existe (CDC, arts. 6º, 14, 30 e 31), mas ele se mede
> nesses termos, não pelo prejuízo isolado.
>
> Como a responsabilidade é avaliada: wikijuridica.com.br/consumidor/agencia-nao-avisou-visto-documentacao/

---

## 3. Antes de publicar cada peça

- **Conferir a vigência na fonte oficial no dia da redação.** As cinco se apoiam
  em norma estável, mas "estável" não é "imutável", e o post não se corrige.
- **Não prometer resultado nem frequência.** "Você vai receber", "garantimos",
  "toda semana" — nada disso. O que se afirma é o que a norma diz.
- **Manter o link para a página do acervo.** É ele que sustenta a peça: o post
  é o resumo, a página é a fonte com proveniência auditável.
- **Sem caso de cliente**, ainda que anonimizado.
