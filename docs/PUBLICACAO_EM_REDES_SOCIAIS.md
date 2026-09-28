# Publicar nas redes sociais do portal

Como criar e publicar peças nos perfis oficiais. **Leia isto antes de escrever
qualquer seletor** — cada armadilha aqui custou uma execução inteira de
navegador para ser descoberta, e várias custaram cinco.

## O caminho, em três comandos

```bash
./tools/publicar-perfis-sociais --login                        # uma vez, o titular autentica
./tools/publicar-perfis-sociais --rede facebook --todas --dry-run
./tools/publicar-perfis-sociais --rede facebook --todas
```

Redes: `facebook` · `instagram` · `linkedin`. **Idempotente por (rede, peça)** —
o que já foi publicado não republica; o registro fica em
`tools/publicador-social/estado.jsonl`, versionado.

## Criar peças novas

1. **Escolher do acervo, nunca inventar.** `content/pages.json` tem 6.841
   páginas publicadas com FAQ e título curto; cada `faq[].question` já é um post
   pronto (pergunta concreta + resposta com base legal + link).
2. **Preferir norma estável.** Post em rede social **não se corrige depois de
   publicado** como página se corrige. Descarte gancho que dependa de norma
   recente ou em trânsito, e confira a vigência na fonte oficial no dia.
3. **Editar `.agents/runtime/artes-perfis-<data>/gerar-artes.py`** (o dicionário
   `PECAS`) e rodar. As artes saem 1080×1350 em navy `#0F1D2E` + dourado
   `#C6A253` + serifada — as mesmas do site, para quem chega pelo post
   reconhecer a página.
4. **`legendas.md` é a fonte única do texto** — o publicador lê dali. Duplicar a
   legenda no código criaria duas versões que divergem na primeira correção.

**Ética (Prov. OAB 205/2021 e art. 44, §1º do CED):** toda arte leva
"Responsável técnico: Rafael Toledo — OAB/RJ 227191", porque arte que circula
sozinha é publicidade. Sem promessa de resultado, sem preço, sem "consulte-nos".
E **nada de frequência** ("acompanhe", "toda semana") — num perfil sem histórico
isso é afirmação falsa.

## Isolamento: `:99`, nunca `:0`

O navegador do agente roda em **Xvfb `:99`**
([ADR](adr/2026-08-27-xvfb-display-virtual-para-agente.md)). O wrapper força
isso sozinho; a **única** exceção é `--login`, onde o titular digita credencial
vendo a tela.

**Não é preferência, é contenção.** O `:0` tem uma VM anexada por
`virt-viewer --attach` com **PJe/e-SAJ e o token de assinatura** — e
`virt-viewer` encaminha teclado e mouse para dentro do guest. Em `:99` isso é
inalcançável **por construção**: são servidores X distintos, com sockets
distintos (`X0` e `X99`). Medido: `:0` tem 9 janelas, `:99` tem zero.

## O método que funciona: fotografar, não chutar

Corrigir seletor por tentativa revela **um** defeito por execução. Cinco
tentativas se perderam assim antes de eu parar e fotografar.

- **Toda falha grava foto** (`falha-<rede>-<peça>.png`) e linha no
  `estado.jsonl`. Foi isso que transformou "timeout no seletor" — que não diz
  nada — em defeitos nomeados.
- **`olhar-pagina.mjs`** percorre o fluxo e fotografa cada etapa sem publicar.
- **`gravar-fluxo.mjs`** grava os cliques do titular, quando o caminho é
  desconhecido.
- **`diagnosticar.mjs`** lista os botões de **todos** os `[role=dialog]` — o
  Facebook empilha composer e editor de foto, e medir só o último (`.pop()`)
  mostra um modal com um botão só.

## Armadilhas por rede, todas medidas

### Facebook

| Armadilha | O que acontece |
|---|---|
| **"Compartilhe um pensamento" é NOTAS** | Não é o composer. Abre um modal com "Escolha um emoji" e "Compartilhar nota". O composer é **"No que você está pensando"**. |
| **O botão final chama "Postar"** | Não "Publicar". Cinco tentativas morreram nessa palavra. A tela é "Configurações do post", com "Salvar" e "Postar". |
| **"Turbine esse post" = ANÚNCIO PAGO** | O texto do toggle diz *"Depois de clicar em **Postar**…"*, e esse `<b>` casa com seletor por texto — o clique **liga o toggle**. Há guarda que lê `aria-checked`, desliga e **aborta** se não conseguir. |
| **Dispensar diálogo fecha o composer** | A rotina de dispensa não acha botão de recusa dentro do composer (não há), cai no `Escape`, e o Escape fecha tudo. Ela precisa **reconhecer o composer e não tocar nele**. |
| **"Avançar" é obrigatório com imagem** | Só ele leva à tela que tem o botão final. |

### Instagram

| Armadilha | O que acontece |
|---|---|
| **Não declara `role=button`** | Em nenhum controle do fluxo. Ancore em **texto** ou **`aria-label`**, nunca em papel acessível. |
| **Sidebar colapsa em 1440px** | O rótulo "Create" some do DOM; sobra o ícone. Âncora: `[aria-label="New post"]`. |
| **Dois caminhos para o mesmo lugar** | Sidebar expandida → submenu (Post/Live/Ad); colapsada → modal direto. Tolere os dois. |
| **Número de "Next" varia** | Uma ou duas telas, conforme o formato da imagem. **Avance até a legenda**, não conte passos. |
| **Interface pode estar em inglês** | O idioma é da conta. Aceite PT e EN em todo rótulo. |
| **Rate limit é real, e PERSISTE** | Depois de ~10 tentativas em minutos passa a devolver *"Something went wrong. Please try again."* na etapa de upload, e **não passou nem após 15 min de intervalo**. Medido em 2026-08-27: Facebook 5/5 e LinkedIn 5/5 publicados no mesmo dia, Instagram **0/5**. **Pare** — insistir agrava e leva a bloqueio da conta. |

> ⚠️ **Instagram continua sem publicar por esta via.** O fluxo está codificado e
> chega até a tela de legenda, mas a plataforma barra o upload. Hipóteses não
> descartadas: limite para conta nova sem histórico, ou detecção de automação.
> Antes de tentar de novo: espere horas, não minutos, e prefira publicar
> **uma** peça. Se persistir, a rota é a **Graph API com conta Business**
> (exige migrar o perfil para profissional) ou o app do celular.

### LinkedIn

| Armadilha | O que acontece |
|---|---|
| **Zero `input[type=file]` no DOM** | Não dá para injetar arquivo. Medido. |
| **Entre pelo botão "Foto"** | Não por "Começar publicação": "Foto" abre o composer **já pedindo o arquivo**, e o `filechooser` do Playwright intercepta. É o que faz o fluxo funcionar. |

## Regras que valem para as três

1. **`page.screenshot()`, nunca `scrot` da tela.** Ver a *página* resolve o
   problema (o seletor que não acha o botão); ver a *tela* traria junto o risco
   de clicar no terminal ao lado.
2. **Seletor de estrutura > rótulo acessível.** `[contenteditable=true][role=textbox]`
   sobrevive; `getByRole('textbox', {name})` quebra quando o nome muda depois do
   upload.
3. **`.last()` nos contenteditable** — o composer de trás continua montado.
4. **Imagem antes do texto** no Facebook: o upload remonta o composer e um texto
   digitado antes se perde.
5. **Confirme que publicou.** Exit code não é prova: cheque que o composer
   fechou, e confirme o post no perfil.
6. **Nunca aceite diálogo, só recuse.** Aceitar muda configuração da conta do
   titular.
7. **`clicarPorTexto` mira o centro da caixa** (`boundingBox`), porque o botão
   pode não ter papel nenhum.

## Quando um seletor quebrar

As três redes mudam de layout sem aviso. A peça que falha fica **pendente** com
o motivo e a foto; as publicadas são puladas. Corrija o seletor da rota afetada
e repita o comando — **não recomece do zero**.

Se estiver perdido: rode `olhar-pagina.mjs`, leia as fotos, corrija. Uma rodada
de medição vale cinco de tentativa.
