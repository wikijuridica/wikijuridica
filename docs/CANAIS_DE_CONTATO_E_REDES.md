# Canais de contato e redes sociais

Como o portal fala com o visitante e como ele se identifica para o buscador. Dois
canais, dois mecanismos diferentes, nenhum deles com o valor escrito no código.

## WhatsApp

**Onde o número vive:** `.env.local`, variável `WIKI_WHATSAPP_PHONE`, formato
E.164 sem `+` (ex.: `5521999999999`). O arquivo NÃO é versionado. Nenhuma página,
template ou config do repositório contém o número — `TestNumeroConfiguradoNaoAparecEmNenhumArquivoVersionado`
(`internal/contract/cta/contact_channel_contract_test.go`) reprova se aparecer.

**Como é resolvido:** `internal/contactchannel.Resolve` lê primeiro o ambiente do
processo e depois `.env.local`, a partir da raiz do projeto. Trocar o número é
editar essa linha e republicar.

**Comportamento sem o número:** o canal fica não-configurado e o botão
simplesmente não é emitido — nunca vira placeholder nem link quebrado. A
publicação (`cmd/publish-v2-direct`) aborta se o número for INVÁLIDO, mas segue
se ele estiver AUSENTE.

> ⚠️ Consequência a conhecer: republicar sem `.env.local` gera as 9.400 páginas
> sem canal de atendimento, com boot verde e nenhum alarme. É perda comercial
> silenciosa. Antes de republicar em máquina nova, confirme:
> `grep -c WIKI_WHATSAPP_PHONE .env.local`

**Onde aparece:** botão flutuante em toda página jurídica (`renderWhatsAppFloat`,
`internal/render/render.go`). O rótulo muda com a faixa editorial — em página de
faixa comercial é "Falar com o advogado"; em faixa informativa (BPC, gratuidade,
assistência pública) vira "Tirar uma dúvida", sem verbo de contratação, porque o
Provimento OAB 205/2021 veda captação em torno de serviço a que a pessoa tem
direito gratuito.

**Mensagem de origem:** desde 2026-08-06 o link carrega `?text=` com a página de
onde a pessoa veio ("Olá! Vim da página “…” (/area/slug/) e queria tirar uma
dúvida."). Sem isso chega uma conversa em branco e não há como saber que conteúdo
gera procura — o único sinal de retorno disponível enquanto não existe medição de
conversão. Custo medido: 454 bytes de HTML por página, com teto em
`internal/render/wa_float_budget_test.go`.

## Perfis oficiais — como estão ligados

**Ligados desde 2026-08-27.** `content/site.json` declara os três perfis, e eles
saem em duas camadas: no JSON-LD (sinal de entidade para o buscador) e no corpo
visível de `/sobre/`.

```json
"editorial_identity": {
  "author_name": "Rafael Toledo",
  "oab_section": "RJ",
  "oab_number": "227191",
  "source": "project_owner_declared_config",
  "same_as": ["https://www.linkedin.com/in/rafaeltoledoadvogado"],
  "organization_same_as": [
    "https://www.instagram.com/wiki.juridica/",
    "https://www.facebook.com/wikijuridica"
  ]
}
```

### Por que são DOIS campos

O grafo resolve **duas entidades** com `@id` distintos: o Person (`#autor`), que
é Rafael Toledo, e a Organization (`#organization`), que é a Wiki Jurídica.

- `same_as` → perfis da **pessoa** → `Person.sameAs` (o LinkedIn).
- `organization_same_as` → perfis da **marca** → `Organization.sameAs` e
  `LegalService.sameAs` (Instagram e Facebook).

Um só campo atribuiria o perfil "@wiki.juridica" à pessoa física, e o nome do
perfil contradiria o nome do Person na mesma frase do grafo. `sameAs` existe
para reconciliar entidade — declarar a reconciliação errada desperdiça o sinal
em vez de somá-lo. `TestPerfilDaMarcaNaoVaiParaOPersonEViceVersa` pina a
separação, porque os dois campos emitem a mesma chave e uma troca passaria
despercebida na revisão.

### Onde cada coisa aparece, e o que custa

| Camada | Rota | Custo nas 10.107 páginas |
|---|---|---|
| `Organization.sameAs` + `LegalService.sameAs` | home | zero byte |
| `Person.sameAs` (founder e ProfilePage) | home e `/sobre/` | zero byte |
| Bloco visível (`renderPerfisOficiais`) | `/sobre/` | zero byte |

**O custo é zero porque `Article.author` NÃO carrega `sameAs`** — o Person do
artigo recebe `@id`, nome, jobTitle e credencial, nunca perfis. Preencher os
campos muda duas URLs, não dez mil.

**O bloco visível fica só em `/sobre/` por desenho, e não por economia.** Toda
página do acervo já linka `/sobre/#autor` pelo byline `rel="author"`, então os
perfis estão a **um clique** de todas elas sem custar um byte a nenhuma. No
rodapé custaria 10.112 re-datações de uma vez — o acervo inteiro afirmando
revisão jurídica que não ocorreu, que `check-lastmod-causalidade` reprova como
data fabricada e que, numa página assinada por advogado, é problema de ética
antes de ser de SEO.

### O que a validação faz — e o que ela NÃO faz

`internal/structureddata` exige HTTPS, recusa credencial embutida, fragmento,
porta diferente de 443 e duplicata semântica. Desde 2026-08-27 a mesma régua
(`sameAsIssues`) roda nos **três** emissores; antes valia só para o Organization,
e uma URL recusada ali saía inteira no LegalService e na ProfilePage, porque
esses validavam por JSON Schema — onde `format: "uri"` não é assertivo.

> ⚠️ **URL inválida NÃO reprova o build.** Esta página afirmava o contrário até
> 2026-08-27, e era falso. `render.go:620` e `:632` são
> `if report.Passed() && script != ""`, sem ramo de erro: validação que falha faz
> o bloco **não sair**, em silêncio. A home perderia `Organization` e
> `LegalService` sem que nada acusasse — os gates de dado estruturado só cobrem
> página com `Article`, e a home não tem Article.
>
> A defesa é `tools/check-identidade-da-home`, que exige os nós no HTML servido e
> confere que todo perfil declarado chegou lá. **Rode-o depois de publicar.**

`canonicalSameAsKey` **não normaliza barra final nem `www.`**: grave a URL
exatamente na forma que responde 200, senão o mesmo perfil vira duas identidades.

### Trocar ou remover um perfil

Editar `content/site.json`, publicar e **purgar a borda manualmente**:
`tools/purge-edge-cache --url / --url /sobre/`. Essas duas rotas saem **sem
`Cache-Tag`**, então `--tag wj-acervo` não as alcança, e a borda declara
`s-maxage=604800` — sem a purga, a versão antiga fica servida por até sete dias.

### O cartão social da home

Até 2026-08-27 a home era a **única** das 10.335 páginas sem `og:image`: a
derivação de área devolvia `false` para `/`, porque um cartão "do site inteiro"
seria hardcode por rota. Quando a raiz virou o endereço divulgado nos perfis,
ela passou a ser a URL mais compartilhada do portal — e compartilhá-la produzia
card sem imagem. `socialcard.AreaDaRaiz` deriva o nome da **marca**
(`"Wiki Jurídica"` → `wiki-juridica`), sem literal de rota, e
`AreaDoCaminhoOuRaiz` é a derivação única que o emissor do `og:image` e o
materializador do PNG compartilham. Divergir ali é como a tag passa a apontar
para um arquivo que ninguém gerou, com o 404 cacheado sete dias.

### Conteúdo dos perfis

Os textos de bio e as peças de estreia estão em
[`CONTEUDO_PERFIS_SOCIAIS.md`](CONTEUDO_PERFIS_SOCIAIS.md), com a exigência do
art. 44, §1º do Código de Ética (nome e inscrição na OAB na publicidade
profissional) já incorporada.
