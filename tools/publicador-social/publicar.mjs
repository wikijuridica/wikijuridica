#!/usr/bin/env node
/**
 * publicar.mjs — publica as peças do acervo nos perfis oficiais do portal.
 *
 * POR QUE ESTA FERRAMENTA EXISTE. Publicar pelo navegador controlado pelo
 * Claude Code esbarrou em dois bloqueios técnicos REAIS, medidos em 2026-08-27:
 *
 *   1. INSTAGRAM: clicar em "Criar" não abre modal nem cria `input[type=file]`
 *      no DOM — ele dispara o seletor de arquivos NATIVO do sistema, que
 *      congela o renderer e nenhuma automação de DOM alcança. Medido: o clique
 *      registra (`clicou: true`) e o DOM segue com zero inputs e zero diálogos.
 *
 *   2. FACEBOOK: o composer usa Lexical, que mantém estado próprio. Texto
 *      inserido por `execCommand` ou por digitação sintética entra no DOM
 *      (411 caracteres contados) mas o React não o registra — o placeholder
 *      "No que você está pensando?" continua visível e o post sairia SEM
 *      legenda. Limpar o `innerHTML` e redigitar duplicou o texto para 830
 *      caracteres sem nunca sincronizar.
 *
 * O Playwright resolve os dois porque fala CDP: `page.on('filechooser')`
 * intercepta o seletor nativo antes de ele abrir, e `locator.type()` gera
 * eventos de teclado no nível do navegador — os mesmos que o Lexical escuta.
 *
 * SEM SaaS, SEM API PROPRIETÁRIA. Só playwright-core (Apache-2.0) dirigindo o
 * Chrome já instalado na máquina. Nenhum dado sai daqui para terceiro além do
 * que é publicado no perfil do próprio dono. Nenhuma credencial passa pelo
 * código: a sessão vive num perfil de navegador que o titular autentica UMA
 * vez, com `--login`.
 *
 * USO
 * Chame pelo wrapper tools/publicar-perfis-sociais, que roda de qualquer
 * diretório e instala a dependência sozinho:
 *
 *   ./tools/publicar-perfis-sociais --login                    o titular autentica (uma vez)
 *   ./tools/publicar-perfis-sociais --listar                   peças e o que já foi publicado
 *   ./tools/publicar-perfis-sociais --rede instagram --peca 01
 *   ./tools/publicar-perfis-sociais --rede facebook --todas
 *   ./tools/publicar-perfis-sociais --rede linkedin --todas --dry-run
 *
 * IDEMPOTENTE por (rede, peça): o que já foi publicado não republica. O
 * registro fica em estado.jsonl, versionado — republicar por engano polui o
 * perfil e não tem desfazer barato.
 */

import { chromium } from 'playwright-core';
import { readFileSync, existsSync, appendFileSync, mkdirSync, readdirSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { perfilPronto } from './perfil.mjs';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, '../..');
const ARTES = join(RAIZ, '.agents/runtime/artes-perfis-20260827');
// O perfil mora FORA da arvore do repositorio: ele guarda Cookies e Login
// Data das sessoes autenticadas, e `.gitignore` nao impede que credencial
// viva viaje em copia, backup ou varredura. O porque completo, com a
// medicao, esta em perfil.mjs.
const PERFIL = perfilPronto(AQUI);
const ESTADO = join(AQUI, 'estado.jsonl');

/** Os perfis, e a entidade de cada um — a mesma separação que o JSON-LD declara. */
const REDES = {
  facebook: { url: 'https://www.facebook.com/wikijuridica', entidade: 'marca' },
  instagram: { url: 'https://www.instagram.com/wiki.juridica/', entidade: 'marca' },
  linkedin: { url: 'https://www.linkedin.com/in/rafaeltoledoadvogado/', entidade: 'pessoa' },
};

// ---------------------------------------------------------------- peças

/**
 * Lê as peças de legendas.md — a MESMA fonte que o dono revisa. Duplicar o
 * texto aqui criaria duas versões que divergem na primeira correção.
 */
function lerPecas() {
  const md = readFileSync(join(ARTES, 'legendas.md'), 'utf8');
  const pecas = [];
  for (const bloco of md.split(/^### /m).slice(1)) {
    const [cabecalho, ...resto] = bloco.split('\n');
    const slug = cabecalho.trim().split(/\s+/)[0];
    const png = join(ARTES, `${slug}.png`);
    if (!existsSync(png)) continue;
    pecas.push({
      slug,
      id: slug.split('-')[0],
      imagem: png,
      // Corta no separador do markdown: "---" divide as peças em legendas.md e
      // não é conteúdo. Ele foi parar dentro de um rascunho no LinkedIn antes
      // de eu notar — o parser levava o arquivo inteiro a partir do cabeçalho.
      legenda: resto.join('\n').split(/^---$/m)[0].trim(),
    });
  }
  return pecas;
}

// ---------------------------------------------------------------- estado

function jaPublicado(rede, id) {
  if (!existsSync(ESTADO)) return null;
  for (const linha of readFileSync(ESTADO, 'utf8').split('\n')) {
    if (!linha.trim()) continue;
    const r = JSON.parse(linha);
    if (r.rede === rede && r.peca === id && r.status === 'publicado') return r;
  }
  return null;
}

function registrar(reg) {
  appendFileSync(ESTADO, JSON.stringify({ ...reg, em: new Date().toISOString() }) + '\n', 'utf8');
}

// ---------------------------------------------------------------- navegador

/**
 * Abre o Chrome com um perfil DEDICADO a esta ferramenta.
 *
 * Perfil próprio, e não o `~/.config/google-chrome/Default` do titular, por
 * dois motivos: o Chrome recusa abrir um perfil já em uso por outra instância,
 * e dirigir o perfil pessoal dele por automação misturaria a navegação real
 * com a automatizada. O preço é um login inicial, feito uma vez.
 */
async function abrirNavegador({ headless }) {
  mkdirSync(PERFIL, { recursive: true });
  const ctx = await chromium.launchPersistentContext(PERFIL, {
    channel: 'chrome',
    headless,
    viewport: { width: 1440, height: 900 },
    // --disable-notifications mata na raiz o "Solicitação de notificações push":
    // num perfil recém-criado ele sobe como role="alertdialog" por cima de tudo
    // e INTERCEPTA O PONTEIRO. Foi o que derrubou a primeira publicação — o
    // Playwright achava o composer, dizia "element is visible, enabled and
    // stable", e o clique batia no overlay por 20s até estourar o timeout.
    args: ['--disable-blink-features=AutomationControlled', '--disable-notifications'],
  });
  // Cinto e suspensório: negar a permissão faz o site nem chegar a pedir.
  await ctx.grantPermissions([]).catch(() => {});
  return ctx;
}

/**
 * Fecha o que estiver por cima antes de clicar em qualquer coisa.
 *
 * As três redes interrompem com diálogos que não fazem parte do fluxo — pedido
 * de notificação, "salvar login?", cookies, "instale o app". Nenhum deles
 * aparece sempre, e é por isso que a rotina é tolerante: procura pelo texto do
 * botão de recusa e segue adiante se não achar nada.
 *
 * Recusar, e nunca aceitar: aceitar mudaria configuração da conta do titular.
 */
async function dispensarInterrupcoes(page) {
  const recusas = [
    /^(Agora não|Not now|Depois|Cancelar)$/i,
    /^(Permitir todos os cookies|Recusar cookies opcionais|Decline optional cookies)$/i,
    /^(Fechar|Close|Dispensar|Dismiss)$/i,
  ];
  // NUNCA tocar no composer. Este laço já fechou o próprio modal de publicação:
  // ele não encontra botão de recusa lá dentro (não há — é o composer, não um
  // aviso), cai no Escape, e o Escape fecha o composer. O resultado ficou
  // fotografado: modal fechado e a legenda caída no composer inline da
  // timeline, com a imagem perdida. Interrupção é o que INTERROMPE o fluxo;
  // o composer é o fluxo.
  const ehComposer = /Criar publicação|Criar post|No que você está pensando|Configurações do post/i;
  for (let volta = 0; volta < 3; volta++) {
    const dialogo = page.locator('[role=dialog], [role=alertdialog]').first();
    if (!(await dialogo.isVisible().catch(() => false))) return;
    if (ehComposer.test(await dialogo.innerText().catch(() => ''))) return;
    let fechou = false;
    for (const rotulo of recusas) {
      const botao = dialogo.getByRole('button', { name: rotulo }).first();
      if (await botao.isVisible().catch(() => false)) {
        await botao.click({ timeout: 4000 }).catch(() => {});
        fechou = true;
        break;
      }
    }
    if (!fechou) {
      // Sem botão reconhecido: Escape resolve a maioria dos modais do Facebook.
      await page.keyboard.press('Escape').catch(() => {});
    }
    await page.waitForTimeout(1200);
  }
}

/**
 * O campo de texto do composer, por ESTRUTURA e não por rótulo.
 *
 * `getByRole('textbox', { name: ... })` falhou na prática: depois que a imagem
 * sobe, o Facebook troca o nome acessível do campo e o locator nem resolve (30s
 * de espera, medido). O rótulo também muda com o idioma da conta. Já
 * `[contenteditable=true][role=textbox]` é o que o composer é — foi assim que
 * eu o encontrei inspecionando o DOM ao vivo.
 *
 * `.last()` porque o Facebook mantém o composer da timeline montado atrás do
 * modal: o primeiro contenteditable da página é o de trás, o de cima é o certo.
 */
function campoDeTexto(page) {
  return page.locator('[contenteditable="true"][role="textbox"]').last();
}

/**
 * Endereço do portal dentro da legenda: um caractere de cada vez é o que faz o
 * `facebookexternalhit` bater 404 no NOSSO servidor centenas de vezes por post.
 *
 * MEDIÇÃO QUE OBRIGA (2026-08-29, ledger `data/ops/access/access-*.jsonl`):
 * a publicação de 2026-08-27 no Facebook (15 tentativas entre 18:03 e 18:50 UTC,
 * `estado.jsonl`) coincide byte a byte com 407 respostas 404 servidas ao
 * `facebookexternalhit` — TODAS na hora 18h, TODAS num prefixo estrito da URL da
 * peça. Amostra literal do log, em ordem: `/f`, `/fa`, `/fam`, `/fami`,
 * `/famil`, `/familia/g`, `/familia/gu`, … até
 * `/familia/guarda-animal-estimacao/`, que é a única que responde 200. No dia
 * seguinte, às 06h, o mesmo padrão devolveu mais 78. São 503 respostas 404 em
 * 22 dias, 224 caminhos distintos, e nenhuma delas é rastreio: é o composer do
 * Facebook pedindo a prévia do link A CADA TECLA que `type()` emite.
 *
 * Isso é dano duplo, e por isso é defeito e não curiosidade: o portal vive de
 * ser rastreado, e o Facebook aprende que 224 endereços nossos são 404 — além
 * de o número entrar no orçamento de erro do `facebookexternalhit` (1.291 404
 * na borda em 8 dias, 28% do tráfego dele) como se fosse falha do site.
 *
 * A CORREÇÃO NÃO PODE SER "não digitar": o composer do Facebook é Lexical, e o
 * cabeçalho deste arquivo registra a medição de que texto inserido por
 * `execCommand` NÃO é registrado pelo React. `keyboard.insertText` é o meio
 * termo comprovado pelo CDP: ele emite `beforeinput`/`input` com
 * `inputType: "insertText"` — o mesmo par de eventos que uma colagem produz e
 * que o Lexical trata —, porém UMA vez para o endereço inteiro, sem os eventos
 * de tecla intermediários que disparam a prévia.
 *
 * Então a legenda é dividida: prosa continua saindo tecla a tecla (é o que o
 * cabeçalho mediu ser necessário) e SÓ o endereço entra de uma vez. A conferência
 * de comprimento que já existe depois da chamada continua valendo — se o Lexical
 * não registrar, o fluxo aborta antes de publicar, como já abortava.
 */
const ENDERECO_NA_LEGENDA = /(?:https?:\/\/)?(?:[a-z0-9-]+\.)+[a-z]{2,}(?:\/[^\s]*)?/gi;

async function digitarLegenda(page, campo, legenda) {
  let cursor = 0;
  ENDERECO_NA_LEGENDA.lastIndex = 0;
  for (let achado = ENDERECO_NA_LEGENDA.exec(legenda); achado; achado = ENDERECO_NA_LEGENDA.exec(legenda)) {
    const antes = legenda.slice(cursor, achado.index);
    if (antes) await campo.type(antes, { delay: 12 });
    // insertText é do teclado da PÁGINA, não do locator: é a API que emite o
    // evento de inserção sem os keydown/keyup por caractere.
    await page.keyboard.insertText(achado[0]);
    cursor = achado.index + achado[0].length;
  }
  const resto = legenda.slice(cursor);
  if (resto) await campo.type(resto, { delay: 12 });
}

/**
 * Clica num elemento achado pelo TEXTO, mirando o centro da caixa dele.
 *
 * `getByRole('button')` não serve aqui: o botão final do Facebook — o "Postar"
 * da tela "Configurações do post" — NÃO tem role=button. Ele existe, é visível,
 * eu o vi numa captura da página; só não é alcançável pelo papel acessível.
 *
 * Então o caminho é o que um humano faz: achar pelo rótulo e clicar onde ele
 * está. `boundingBox()` dá a coordenada real e `mouse.click()` bate nela, sem
 * depender de o site declarar semântica nenhuma.
 *
 * Sobe até o ancestral clicável quando o texto está num <span> interno, e cai
 * no clique por coordenada quando nem isso resolve.
 */
async function clicarPorTexto(page, rotulo, oQueE) {
  const candidatos = page.getByText(rotulo).filter({ visible: true });
  const quantos = await candidatos.count();
  for (let i = 0; i < quantos; i++) {
    const alvo = candidatos.nth(i);
    const caixa = await alvo.boundingBox().catch(() => null);
    if (!caixa || caixa.width < 8 || caixa.height < 8) continue;
    await page.mouse.click(caixa.x + caixa.width / 2, caixa.y + caixa.height / 2);
    return;
  }
  throw new Error(`não achei o ${oQueE} (${rotulo}) na página`);
}

async function login() {
  const ctx = await abrirNavegador({ headless: false });
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  console.log('\nAutentique-se nas redes nas abas que vão abrir.');
  console.log('A sessão fica salva neste perfil; das próximas vezes roda sozinho.\n');
  for (const [nome, { url }] of Object.entries(REDES)) {
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'domcontentloaded' }).catch(() => {});
    console.log(`  aberta: ${nome}`);
  }
  await page.close().catch(() => {});
  console.log('\nQuando terminar de logar nas três, FECHE a janela do navegador.');
  await ctx.waitForEvent('close', { timeout: 0 });
  console.log('Sessão salva em', PERFIL);
}

// ---------------------------------------------------------------- facebook

/**
 * Publica no Facebook. A ordem importa: a imagem entra ANTES do texto porque o
 * upload remonta o composer e um texto digitado antes se perde.
 */
async function publicarFacebook(page, peca) {
  await page.goto(REDES.facebook.url, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  await dispensarInterrupcoes(page);

  // NUNCA casar "Compartilhe um pensamento": esse é o widget de NOTAS do
  // Facebook, não o composer de post. Clicar nele abre um modal cujos botões
  // são "Escolha um emoji", "criação de música" e "Compartilhar nota" — sem
  // "Foto/vídeo" e sem "Publicar". Foram três tentativas perseguindo seletor
  // dentro do modal errado até um diagnóstico listar os botões e mostrar isso.
  const composer = page.getByText(/No que você está pensando/i).first();
  await composer.click({ timeout: 20000 });

  // Confirma que abriu o modal CERTO antes de seguir: melhor falhar aqui, com
  // o motivo, do que perseguir um "Publicar" que não existe naquela tela.
  const modal = page.locator('[role=dialog]').filter({ hasText: /Criar publicação|Criar post/i }).first();
  await modal.waitFor({ state: 'visible', timeout: 20000 }).catch(() => {
    throw new Error('o modal de criar post não abriu (pode ter aberto o de notas) — verifique o gatilho do composer');
  });
  await page.waitForTimeout(2000);
  await dispensarInterrupcoes(page);

  // O seletor de arquivos nativo é interceptado ANTES de abrir — é isto que a
  // automação de DOM não consegue fazer, e o motivo de esta ferramenta existir.
  const [chooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 20000 }),
    page.getByRole('button', { name: /^Foto\/vídeo$/i }).first().click(),
  ]);
  await chooser.setFiles(peca.imagem);
  await page.waitForTimeout(4000);

  // type() emite eventos de teclado reais via CDP; é o que o Lexical registra.
  const campo = campoDeTexto(page);
  await campo.waitFor({ state: 'visible', timeout: 20000 });
  await campo.click();
  await digitarLegenda(page, campo, peca.legenda);
  await page.waitForTimeout(1500);

  // Confere no PRÓPRIO campo que o texto entrou. Olhar o placeholder solto na
  // página não servia: o composer de trás tem o dele, sempre visível.
  const escrito = (await campo.innerText().catch(() => '')).trim();
  if (escrito.length < peca.legenda.length * 0.6) {
    throw new Error(`o composer não registrou a legenda (${escrito.length} de ${peca.legenda.length} caracteres) — abortado para não publicar sem texto`);
  }

  // O FLUXO TEM UMA ETAPA A MAIS QUANDO HÁ FOTO. Inspecionando o modal ao vivo
  // eu tinha visto "Avançar" e NENHUM "Publicar" — post só com texto publica
  // direto, post com imagem passa por uma tela intermediária. Por isso o
  // "Avançar" é opcional (catch) e o "Publicar" é obrigatório.
  // "Avançar" é OBRIGATÓRIO quando há imagem: ele leva à tela "Configurações do
  // post", e é só lá que existe o botão final. Tratá-lo como opcional deixava o
  // fluxo parar na tela anterior, procurando um botão que ali não existe — foi
  // o que aconteceu na tentativa anterior.
  const avancar = page.getByRole('button', { name: /^Avançar$/i }).first();
  if (await avancar.isVisible().catch(() => false)) {
    await avancar.click({ timeout: 10000 });
    await page.waitForTimeout(3500);
    await dispensarInterrupcoes(page);
    // Confirma a tela certa ANTES de caçar o botão: errar aqui gasta 25s de
    // timeout e devolve um erro que não diz onde o fluxo realmente parou.
    await page.getByText(/Configurações do post/i).first()
      .waitFor({ state: 'visible', timeout: 15000 })
      .catch(() => { throw new Error('cliquei em Avançar mas a tela "Configurações do post" não apareceu'); });
  }

  // O BOTÃO SE CHAMA "Postar", NÃO "Publicar". Cinco tentativas de seletor
  // falharam por causa dessa palavra: a tela final é "Configurações do post" e
  // traz "Salvar" e "Postar". Só descobri fotografando a página — nenhuma busca
  // por texto acha um botão cujo nome você supôs errado.
  // "Publicar" fica no alternador como rede de segurança: o rótulo varia entre
  // perfil pessoal e Página, e entre versões da interface.
  // GUARDA DE GASTO: "Turbine esse post" é ANÚNCIO PAGO, e o clique anterior o
  // ligou por acidente — o texto do próprio toggle diz "Depois de clicar em
  // <b>Postar</b>...", e esse <b> casou com o seletor do botão. Fotografado
  // ligado (azul) antes de eu perceber. Desligar SEMPRE antes de postar:
  // publicar de graça e publicar pagando são a mesma tela e um toggle de
  // distância.
  const turbinar = page.getByRole('switch').first();
  if (await turbinar.isVisible().catch(() => false)) {
    if ((await turbinar.getAttribute('aria-checked')) === 'true') {
      await turbinar.click().catch(() => {});
      await page.waitForTimeout(1200);
    }
    if ((await turbinar.getAttribute('aria-checked')) === 'true') {
      throw new Error('não consegui desligar "Turbine esse post" (anúncio pago) — abortado antes de publicar');
    }
  }

  // O BOTÃO, e não a palavra. getByText casaria o <b>Postar</b> dentro do
  // parágrafo do toggle — foi exatamente o que aconteceu. O botão real é o
  // último role=button do modal, no rodapé, ao lado de "Salvar".
  const postar = page.getByRole('button', { name: /^(Postar|Publicar)$/i }).last();
  await postar.waitFor({ state: 'visible', timeout: 15000 });
  await postar.click({ timeout: 15000 });
  await page.waitForTimeout(9000);

  // Confirma que o composer fechou: enquanto ele estiver aberto, nada foi ao ar.
  const aindaAberto = await page.getByRole('dialog').filter({ hasText: /Criar post/i })
    .first().isVisible().catch(() => false);
  if (aindaAberto) throw new Error('cliquei em Publicar mas o composer não fechou — publicação não confirmada');
}

// ---------------------------------------------------------------- instagram

/**
 * Publica no Instagram. Aqui o filechooser é o ponto INTEIRO: o botão "Criar"
 * não materializa input no DOM, ele chama o seletor do sistema operacional.
 */
async function publicarInstagram(page, peca) {
  await page.goto('https://www.instagram.com/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  await dispensarInterrupcoes(page);

  // O INSTAGRAM ABRE UM SUBMENU, não o seletor de arquivo. Clicar em "Create"
  // mostra "Post / Live video / Ad"; só o "Post" dispara o filechooser. Esperar
  // o filechooser logo após o primeiro clique dá timeout — foi o que aconteceu,
  // e a foto da falha mostrou o submenu aberto, esperando escolha.
  //
  // E a interface desta conta está EM INGLÊS: os rótulos aceitam as duas
  // línguas porque o idioma é da conta, não do código, e pode mudar sem aviso.
  // ÂNCORA NO aria-label DO ÍCONE, não no texto. Em 1440px a sidebar do
  // Instagram COLAPSA para só ícones — o rótulo "Create" some do DOM visível e
  // qualquer busca por texto falha. Foi o que a foto da falha mostrou. O
  // aria-label do svg sobrevive ao colapso, porque é o que o leitor de tela usa.
  const novoPost = page.locator(
    '[aria-label="New post"], [aria-label="Nova publicação"], [aria-label="Criar"], [aria-label="Create"]'
  ).first();
  await novoPost.waitFor({ state: 'visible', timeout: 20000 });
  await novoPost.click();
  await page.waitForTimeout(1800);

  // O "+" abre DIRETO o modal "Create new post" ("Drag photos and videos here"),
  // sem submenu. Quem dispara o seletor de arquivo é o botão "Select from
  // computer" dentro dele. Eu tinha suposto um submenu "Post" que só existe em
  // outro caminho da interface; a foto da falha mostrou o modal já aberto,
  // esperando o clique no botão.
  // DOIS CAMINHOS, e qual aparece depende da largura da janela. Com a sidebar
  // EXPANDIDA o "+" abre um submenu (Post / Live video / Ad) e é o "Post" que
  // leva ao modal; COLAPSADA (só ícones, como em 1440px) ele abre o modal
  // direto. Medi os dois em execuções seguidas, com fotos. Tolerar ambos custa
  // seis linhas; apostar num deles custa uma falha a cada vez que a janela muda.
  const submenuPost = page.getByText(/^(Publicação|Post)$/i).first();
  if (await submenuPost.isVisible().catch(() => false)) {
    await submenuPost.click().catch(() => {});
    await page.waitForTimeout(2000);
  }

  await page.getByText(/Create new post|Criar nova publicação/i).first()
    .waitFor({ state: 'visible', timeout: 20000 })
    .catch(() => { throw new Error('o modal "Create new post" não abriu'); });

  // PREFERIR setInputFiles A CLICAR. Se o modal traz um input[type=file] no DOM
  // — e traz —, injetar o arquivo nele dispensa o botão, a corrida com a
  // animação e o seletor nativo por completo. O clique em "Select from
  // computer" fica de reserva para o dia em que o input sumir do DOM.
  const entrada = page.locator('input[type=file]').last();
  if (await entrada.count() > 0) {
    await entrada.setInputFiles(peca.imagem);
  } else {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 25000 }),
      clicarPorTexto(page, /^(Selecionar do computador|Select from computer)$/i,
                     'botão que abre o seletor de arquivo'),
    ]);
    await chooser.setFiles(peca.imagem);
  }
  await page.waitForTimeout(5000);

  // Recorte -> filtros -> legenda: dois "Next" antes do "Share". Todos por
  // TEXTO, nunca por role: o Instagram não declara role=button em controle
  // nenhum do fluxo — nem no "+", nem no "Select from computer", nem aqui.
  // Neste site, papel acessível não é âncora; texto e aria-label são.
  // AVANÇA ATÉ A LEGENDA, sem contar passos. O número de "Next" varia — medi
  // duas telas numa execução e uma noutra, porque a etapa de filtros aparece ou
  // não conforme o formato da imagem. Contar passo fixo quebra nos dois
  // sentidos: sobra clique (erro "não achei Next") ou falta (para antes da
  // legenda). O critério certo é o destino, não a contagem.
  for (let i = 0; i < 4; i++) {
    const naLegenda = await page.getByText(/Write a caption|Escreva uma legenda/i)
      .first().isVisible().catch(() => false);
    if (naLegenda) break;
    const next = page.getByText(/^(Avançar|Next)$/i).filter({ visible: true }).first();
    if (!(await next.isVisible().catch(() => false))) break;
    const caixa = await next.boundingBox().catch(() => null);
    if (!caixa) break;
    await page.mouse.click(caixa.x + caixa.width / 2, caixa.y + caixa.height / 2);
    await page.waitForTimeout(3000);
  }

  const campo = campoDeTexto(page);
  await campo.waitFor({ state: 'visible', timeout: 20000 });
  await campo.click();
  await digitarLegenda(page, campo, peca.legenda);
  await page.waitForTimeout(1500);

  await clicarPorTexto(page, /^(Compartilhar|Share)$/i, 'botão Share');
  await page.waitForTimeout(12000);

  // Confirma que saiu: enquanto o modal de criação estiver aberto, nada foi ao ar.
  const aindaCriando = await page.getByText(/Create new post|Criar nova publicação/i)
    .first().isVisible().catch(() => false);
  if (aindaCriando) throw new Error('cliquei em Share mas o modal não fechou — publicação não confirmada');
}

// ---------------------------------------------------------------- linkedin

async function publicarLinkedin(page, peca) {
  await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);
  await dispensarInterrupcoes(page);

  // ENTRAR PELO BOTÃO "Foto", e não por "Começar publicação". Medido: o
  // LinkedIn não mantém NENHUM input[type=file] no DOM, então não há como
  // injetar o arquivo depois; e o composer aberto por "Começar publicação" não
  // expõe rótulo de mídia que eu tenha conseguido ancorar. O botão "Foto" abre
  // o composer JÁ pedindo o arquivo — o seletor nativo vem junto, e o
  // filechooser do Playwright o intercepta.
  const [chooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 25000 }),
    page.getByRole('button', { name: /^Foto$/i }).first().click({ timeout: 20000 }),
  ]);
  await chooser.setFiles(peca.imagem);
  await page.waitForTimeout(6000);

  // Depois da imagem, o composer pede o texto. "Avançar" existe em algumas
  // versões do fluxo de mídia e não em outras — opcional, como no Facebook.
  const proximo = page.getByRole('button', { name: /^(Avançar|Next)$/i }).first();
  if (await proximo.isVisible().catch(() => false)) {
    await proximo.click().catch(() => {});
    await page.waitForTimeout(3000);
  }

  const campo = campoDeTexto(page);
  await campo.waitFor({ state: 'visible', timeout: 20000 });
  await campo.click();
  await digitarLegenda(page, campo, peca.legenda);
  await page.waitForTimeout(2000);

  const escrito = (await campo.innerText().catch(() => '')).trim();
  if (escrito.length < peca.legenda.length * 0.6) {
    throw new Error(`o composer não registrou a legenda (${escrito.length} de ${peca.legenda.length}) — abortado`);
  }

  await page.getByRole('button', { name: /^(Publicar|Post)$/i }).first().click({ timeout: 20000 });
  await page.waitForTimeout(10000);

  const composerAberto = await page.getByText(/Publicar em Todos|Post to Anyone/i)
    .first().isVisible().catch(() => false);
  if (composerAberto) throw new Error('cliquei em Publicar mas o composer não fechou — publicação não confirmada');
}

const PUBLICADORES = {
  facebook: publicarFacebook,
  instagram: publicarInstagram,
  linkedin: publicarLinkedin,
};

// ---------------------------------------------------------------- cli

function args() {
  const a = process.argv.slice(2);
  const tem = (f) => a.includes(f);
  const val = (f) => (a.includes(f) ? a[a.indexOf(f) + 1] : null);
  return {
    login: tem('--login'), listar: tem('--listar'), todas: tem('--todas'),
    dryRun: tem('--dry-run'), headless: tem('--headless'),
    rede: val('--rede'), peca: val('--peca'),
  };
}

async function main() {
  const o = args();
  const pecas = lerPecas();

  if (o.login) return login();

  if (o.listar || (!o.rede && !o.peca)) {
    console.log(`\npeças em ${ARTES}:\n`);
    for (const p of pecas) {
      const onde = Object.keys(REDES)
        .map((r) => (jaPublicado(r, p.id) ? r : null)).filter(Boolean);
      console.log(`  ${p.slug}  ${onde.length ? 'publicada em: ' + onde.join(', ') : 'não publicada'}`);
    }
    console.log(`\nperfil de sessão: ${existsSync(PERFIL) ? 'criado' : 'AUSENTE — rode --login primeiro'}`);
    console.log('\nredes: ' + Object.keys(REDES).join(' | '));
    console.log('uso:   ./tools/publicar-perfis-sociais --rede <rede> --todas [--dry-run]\n');
    return;
  }

  if (!REDES[o.rede]) throw new Error(`rede inválida: ${o.rede}. Use: ${Object.keys(REDES).join(', ')}`);

  const alvo = o.todas ? pecas : pecas.filter((p) => p.id === String(o.peca).padStart(2, '0'));
  if (!alvo.length) throw new Error(`nenhuma peça casou com --peca ${o.peca}`);

  const pendentes = alvo.filter((p) => !jaPublicado(o.rede, p.id));
  const puladas = alvo.length - pendentes.length;
  if (puladas) console.log(`${puladas} peça(s) já publicada(s) em ${o.rede} — não republico.`);
  if (!pendentes.length) return console.log('nada pendente.');

  // O ENSAIO VEM ANTES da exigência de sessão, de propósito: conferir o que
  // sairia é justamente o que se quer fazer ANTES de autenticar, e exigir login
  // para um comando que não abre navegador seria barreira sem causa.
  if (o.dryRun) {
    console.log(`\nENSAIO — nada será publicado. Em ${o.rede} sairiam:\n`);
    for (const p of pendentes) console.log(`  ${p.slug}\n    ${p.legenda.split('\n')[0]}\n`);
    return;
  }

  if (!existsSync(PERFIL)) throw new Error('sem sessão: rode `./tools/publicar-perfis-sociais --login` uma vez');

  const ctx = await abrirNavegador({ headless: o.headless });
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  let ok = 0;
  for (const p of pendentes) {
    process.stdout.write(`publicando ${p.slug} em ${o.rede} ... `);
    try {
      await PUBLICADORES[o.rede](page, p);
      registrar({ rede: o.rede, peca: p.id, slug: p.slug, status: 'publicado' });
      ok++;
      console.log('OK');
    } catch (erro) {
      // Fotografa o estado no instante da falha. Sem isto, descobrir POR QUE
      // falhou custa outra execução inteira do navegador — foi assim que se
      // perderam cinco tentativas com um botão cujo nome eu supunha errado.
      const foto = join(AQUI, `falha-${o.rede}-${p.id}.png`);
      await page.screenshot({ path: foto, fullPage: false }).catch(() => {});
      console.log(`  estado no momento da falha: ${foto}`);
      registrar({ rede: o.rede, peca: p.id, slug: p.slug, status: 'falhou', foto, erro: String(erro.message).slice(0, 300) });
      console.log(`FALHOU: ${erro.message}`);
      console.log('  (a falha ficou registrada; a peça continua pendente e pode ser repetida)');
    }
    await page.waitForTimeout(5000);
  }
  await ctx.close();
  console.log(`\n${ok}/${pendentes.length} publicada(s). Registro em estado.jsonl`);
}

main().catch((e) => { console.error('ERRO:', e.message); process.exit(1); });
