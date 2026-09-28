# Adoção de `gopkg.in/yaml.v3` para o frontmatter de habilidades

- **Data:** 2026-08-20
- **Estado:** aceita
- **Frente:** Agent Skills Discovery v0.2.0 (`internal/agentskills`)

## Contexto

O formato SKILL.md exige frontmatter YAML, e a biblioteca padrão do Go não tem parser de
YAML. O portal precisa ler frontmatter em dois papéis diferentes:

1. como **publisher**, lendo as próprias habilidades em `content/agent-skills/` — conteúdo
   que nós mesmos escrevemos e que passa por revisão;
2. como **cliente**, lendo `SKILL.md` de origem de terceiro, que pode conter qualquer
   YAML válido (e qualquer YAML inválido).

O papel (2) é o que decide: um parser de subconjunto escrito à mão daria conta das nossas
habilidades e falharia contra o mundo, que é justamente onde o cliente opera.

## Decisão

Adotar `gopkg.in/yaml.v3` na versão **v3.0.1**, com `KnownFields(true)`.

## Alternativas consideradas

**Parser estrito próprio.** O validador oficial usa `strictyaml`, que é mais restrito que
YAML (sem tipagem implícita, sem flow style, sem âncora, sem chave duplicada), então um
parser de subconjunto seria mais próximo do comportamento de referência. Rejeitado pelo
papel (2): o cliente precisa ler o que existe, não o que gostaríamos que existisse.
A restrição extra ficou onde ela pertence — no **validador**, não no parser.

**`go.yaml.in/yaml/v2` ou `gopkg.in/yaml.v2`.** Já presentes como transitivas. Rejeitados:
a v2 não tem `KnownFields`, que é exatamente o mecanismo que faz o campo desconhecido
reprovar como o validador oficial reprova.

## Custo medido

- **Sem rede.** `go.sum:814` já traz o `h1:` de `v3.0.1`, e o módulo já está no cache local
  (`/home/rafael/go/pkg/mod/gopkg.in/yaml.v3@v3.0.1`). O `require` não baixou nada.
- **Licença:** MIT (código do go-yaml) e Apache-2.0 (partes derivadas do libyaml) —
  compatíveis com a política de OSS do repositório.
- **Superfície:** o pacote é usado em um único lugar (`internal/agentskills/frontmatter.go`)
  e só sobre bytes que já passaram por limite de tamanho.

## Consequência operacional

Tocar `go.mod` faz o pre-commit compilar a closure inteira. O commit foi sequenciado com a
sessão que estava editando `internal/httpserver/mcp.go` no mesmo período, e o aviso foi
postado no bus de coordenação antes — commitar sobre árvore alheia em meio-evolução faz o
gate reprovar por trabalho que não é nosso.

## Verificação

`internal/agentskills/frontmatter_test.go` cobre as três armadilhas do parser oficial (byte
zero, delimitador por linha e conjunto fechado de campos), e
`TestCampoDesconhecidoNoFrontmatterReprova` prova que `KnownFields` faz o que se espera
dele.
