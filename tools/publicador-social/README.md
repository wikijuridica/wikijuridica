# Publicador dos perfis oficiais

Publica as peças do acervo no Instagram, Facebook e LinkedIn do portal, sem
SaaS, sem API proprietária e sem nenhuma credencial passando pelo código.

## Uso

```bash
./tools/publicar-perfis-sociais --login                        # UMA vez: o titular autentica as 3 redes
./tools/publicar-perfis-sociais --listar                       # o que existe e o que já foi publicado
./tools/publicar-perfis-sociais --rede facebook --todas --dry-run
./tools/publicar-perfis-sociais --rede facebook --todas        # publica as pendentes
./tools/publicar-perfis-sociais --rede instagram --peca 01     # publica uma
```

**Idempotente por (rede, peça)** — o que já foi publicado não republica. O
registro fica em `estado.jsonl`, versionado: republicar por engano polui o
perfil e não tem desfazer barato.

## Por que esta ferramenta existe

Publicar pelo navegador que o Claude Code controla esbarrou em **dois bloqueios
técnicos reais**, medidos em 2026-08-27 — nenhum deles de permissão:

**Instagram.** Clicar em "Criar" não abre modal nem cria `input[type=file]` no
DOM: dispara o seletor de arquivos **nativo do sistema**, que congela o renderer
e nenhuma automação de DOM alcança. Medido — o clique registra (`clicou: true`)
e o DOM segue com **zero** inputs e **zero** diálogos.

**Facebook.** O composer usa Lexical, que mantém estado próprio. Texto inserido
por `execCommand` ou digitação sintética entra no DOM (411 caracteres contados)
mas o React **não registra**: o placeholder "No que você está pensando?"
continua visível e o post sairia **sem legenda**. Limpar o `innerHTML` e
redigitar duplicou para 830 caracteres sem nunca sincronizar.

O Playwright resolve os dois porque fala CDP:
`page.on('filechooser')` intercepta o seletor nativo **antes** de ele abrir, e
`locator.type()` gera eventos de teclado no nível do navegador — os mesmos que
o Lexical escuta. Por isso `publicarFacebook` aborta se o placeholder continuar
visível depois de digitar: melhor falhar do que publicar imagem sem texto.

## Credenciais

**Nenhuma senha passa pelo código, e nenhuma é lida por ele.** A sessão vive em
`.perfil-navegador/`, um perfil de Chrome que o titular autentica uma vez com
`--login`. O diretório está no `.gitignore` — versioná-lo equivaleria a
commitar as credenciais das três redes.

Perfil dedicado, e não o `~/.config/google-chrome/Default` do titular, por dois
motivos: o Chrome recusa abrir um perfil já em uso por outra instância, e
dirigir o perfil pessoal por automação misturaria a navegação real com a
automatizada.

## Dependência

`playwright-core` 1.49.1 (Apache-2.0), versão fixada. **Não baixa navegador** —
usa o Chrome já instalado (`channel: 'chrome'`), então o custo em disco é um
pacote. Não toca o runtime do portal: é ferramenta de operação, roda fora do
build e fora do serviço.

## Conteúdo

As peças vêm de `.agents/runtime/artes-perfis-20260827/` — `legendas.md` para o
texto e os PNG para a arte. A ferramenta lê **a mesma fonte que o dono revisa**;
duplicar o texto aqui criaria duas versões que divergem na primeira correção.

## Quando um seletor quebrar

As três redes mudam de layout sem aviso, e os seletores são por papel e texto
visível (`getByRole`, `getByText`) justamente para sobreviver a troca de classe
CSS — mas não a redesenho. Quando falhar, a peça continua **pendente** (a falha
é registrada com o motivo em `estado.jsonl`) e basta corrigir o seletor da rota
afetada e repetir o comando: as já publicadas são puladas sozinhas.
