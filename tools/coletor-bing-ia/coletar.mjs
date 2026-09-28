#!/usr/bin/env node
/**
 * coletar.mjs — lê o relatório de DESEMPENHO DE IA do Bing Webmaster Tools, que
 * é onde a Microsoft mostra quantas vezes o portal foi CITADO numa resposta
 * gerada, por página e por dia.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * POR QUE ISTO EXISTE, E POR QUE NÃO É `collect-bing-webmaster`
 *
 * `tools/collect-bing-webmaster` lê a BUSCA CLÁSSICA: `GetQueryStats`,
 * `GetPageStats`, `GetRankAndTrafficStats` — impressão, clique, posição, índice.
 * Citação em resposta gerada não está em nenhum desses endpoints, e apresentar
 * busca clássica como medida de citação de IA é medir na camada errada e
 * entregar o número curto como se fosse o fato.
 *
 * A API PÚBLICA NÃO EXPÕE ESSE DADO, e isso está fechado, não suposto: a
 * interface `IWebmasterApi` lista 62 métodos e nenhum contém `AI`, `Copilot`,
 * `Citation`, `Grounding`, `Generative`, `Chat`, `Answer` ou `LLM`; a página de
 * referência está congelada em 2023-11-14, nunca tocada depois do lançamento do
 * recurso em fev/2026; 28 nomes candidatos foram testados e os 28 devolveram
 * 404; OAuth aponta para o mesmo `api.svc` e os mesmos 62 métodos. Fabrice Canel
 * (Microsoft/Bing), 2026-02-11: *"With this preview, the data is not yet
 * available via the API."*
 *
 * ISSO NÃO É RESSALVA SOBRE O NÚMERO. O número é fato exibido pela Microsoft no
 * painel da conta do titular. "Preview" qualifica a maturidade da API, não a
 * confiabilidade do dado — e ausência de método documentado é problema de
 * engenharia a resolver, nunca razão para não medir. O que falta é NOSSO
 * caminho de leitura, e é ele que esta ferramenta constrói.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * FOTOGRAFE, NÃO CHUTE — o princípio que desenha esta ferramenta
 *
 * O caminho de exportação relatado (`POST /webmasters/api/aiperformance/
 * citationstats/filtered/export`) NÃO ESTÁ PROVADO. Quatro variantes de POST
 * (caminho real, caminho real com a chave de API, caminho INVENTADO e token
 * sintético) devolveram resposta byte a byte idêntica — `400 Could not extract
 * expected anti-forgery token`. O filtro anti-forgery roda ANTES do roteamento,
 * então aquela resposta não distingue rota que existe de rota que não existe.
 *
 * Por isso esta ferramenta NÃO começa mandando o POST que alguém supôs. Ela:
 *
 *   1. abre o painel na sessão do titular e FOTOGRAFA cada etapa
 *      (`page.screenshot`, nunca `scrot` da tela — ver a página resolve o
 *      problema real; ver a tela traz o risco de clicar no terminal ao lado);
 *   2. escuta TODA requisição que o próprio painel dispara (`page.on('request')`)
 *      e anota método, URL, o `x-csrf-token` e o corpo — é o painel que diz qual
 *      é a rota e qual é o formato do pedido, não nós;
 *   3. procura o controle de exportação por papel/texto e clica, para que a
 *      interceptação capture a requisição REAL de exportação;
 *   4. só então REPETE aquela requisição, com o token colhido nesta execução.
 *
 * Corrigir seletor por tentativa revela um defeito por execução — cinco sessões
 * do projeto se perderam assim. O que a ferramenta não achar, ela FOTOGRAFA e
 * REGISTRA, para a próxima execução partir de evidência e não de palpite.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * IDENTIDADE: a tensão está nomeada, e o veredito é pré-registrado
 *
 * Chromium logado manda User-Agent de navegador, e o contrato proíbe sair
 * disfarçado (`TestNenhumPontoDeSaidaSaiDisfarcado`). A proposta, que esta
 * ferramenta IMPLEMENTA E MEDE em vez de afirmar:
 *
 *   ramo 0  o contexto inteiro sai com o UA canônico do WikijuridicaBot.
 *           Resultado possível: o painel nem carrega (SPA que recusa UA
 *           desconhecido), e aí o ramo cai.
 *   ramo 1  navegação com o UA do Chrome (é a sessão do titular, num navegador
 *           de verdade) e o POST de exportação com o UA canônico injetado.
 *           É o ramo PREFERIDO: a requisição que colhe dado se identifica.
 *   ramo 2  exportação com o UA do navegador, se o ramo 1 for recusado.
 *
 * O ramo que valer fica gravado no ledger com o status HTTP e o começo do corpo
 * da resposta, e o motivo da exceção em
 * `internal/wikijuridicabot.NavegadorRealDoTitular` é trocado por esse número.
 * Enquanto a primeira execução autenticada não acontecer, o motivo diz "AINDA
 * NÃO FOI MEDIDO" — porque afirmar medição que não se fez injeta fato falso no
 * trabalho de quem vier depois.
 *
 * A exceção é NOMINAL e sai impressa a cada execução de
 * `tools/check-identidade-de-saida`. Nunca por omissão: foi por omissão que os
 * cinco arquivos do publicador social saíram para Facebook, LinkedIn e Instagram
 * durante meses sem aquele gate sequer contá-los como ponto de saída.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * TETO, E O QUE DELE NÃO ESTÁ MEDIDO
 *
 * Uma execução por dia UTC, no máximo 5 requisições DELIBERADAS (navegação e
 * exportação). As XHR que o próprio painel dispara são consequência de UMA
 * navegação, não pedidos nossos, e por isso não entram no teto — mas entram no
 * registro, contadas, para que ninguém confunda o que pedimos com o que a
 * página pediu por nós.
 *
 * O TETO NÃO ESTÁ MEDIDO, e isso é dito por escrito: os 10 pedidos por 60 s que
 * `collect-bing-webmaster` respeita foram medidos contra `ssl.bing.com`, que é
 * OUTRO HOST, com outro serviço atrás. Limite medido num host não se transfere
 * para outro, e transferi-lo seria apresentar medição alheia como própria. 5 por
 * dia é conservador por construção até que exista medição deste host.
 *
 * ────────────────────────────────────────────────────────────────────────────
 * DUAS FASES, E A SEGUNDA NÃO SE ESCREVE ANTES DA PRIMEIRA
 *
 * FASE 1 (esta) — captura e PRESERVA o CSV cru, grava no ledger uma linha
 * `citacao_ia_export` com o sha256, o tamanho, a contagem de linhas e o
 * CABEÇALHO VERBATIM do CSV. Nada é interpretado.
 *
 * FASE 2 (depois da primeira execução autenticada) — o parser dos campos, e só
 * então as linhas `citacao_ia_diaria`. Escrever o parser antes é inventar
 * esquema: ninguém neste projeto viu ainda o cabeçalho desse CSV, e um parser
 * escrito contra campos imaginados passa verde contra dado que não existe.
 *
 * SAÍDA
 *   exit 0  MEDIU (ou o dia já estava feito, que é execução correta sem trabalho)
 *   exit 1  MEDIU e o resultado é degradado — veredito, não defeito de processo
 *   exit 2  NÃO MEDIU: sessão ausente/expirada, token não colhido, rota não
 *           observada, teto estourado, erro de I/O. "Não rodou" nunca pode ser
 *           confundido com "está tudo certo".
 *
 * USO
 *   tools/collect-bing-ai-citations --login      uma vez, o TITULAR autentica
 *   tools/collect-bing-ai-citations              a rotina diária
 *   tools/collect-bing-ai-citations --forcar     ignora o teto de 1/dia
 *   tools/collect-bing-ai-citations --headless   MEDICAO: o Bing aceita
 *                                                `HeadlessChrome`? Nao e' o
 *                                                padrao, e o porque esta em
 *                                                `coletar()`.
 */

import { chromium } from 'playwright-core';
import { createHash } from 'node:crypto';
import {
  appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync,
  statSync, unlinkSync, writeFileSync,
} from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import process from 'node:process';
import { gzipSync } from 'node:zlib';
import { perfilPronto } from './perfil.mjs';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');

// ─────────────────────────────────────────────────────────── endereços e teto

const SITE = 'https://wikijuridica.com.br/';
const URL_ENTRADA = 'https://www.bing.com/webmasters/home';
// HIPÓTESE DECLARADA, não fato: a rota do painel de Desempenho de IA foi
// relatada, nunca confirmada por nós. Se ela não existir, a navegação cai em
// outra página e o relatório diz isso — com a URL final e a foto.
const URL_PAINEL_IA = 'https://www.bing.com/webmasters/aiperformance';
const TETO_REQUISICOES = 5;

const LEDGER = join(RAIZ, 'data', 'ops', 'bing_webmaster_daily.jsonl');
const ESTADO = join(RAIZ, 'data', 'ops', 'bing_ai_citation_state.json');
const BRUTOS = join(RAIZ, 'data', 'ops', 'bing_ai_citations');
const FOTOS = join(RAIZ, '.agents', 'runtime', 'tela', 'bing-ia');
const SCHEMA = 'bing_webmaster_v1';

// RETENÇÃO DO CRU, decidida ANTES da primeira execução: o CSV é por página e
// por dia sobre ~11 mil páginas, então guardar tudo para sempre é crescimento
// sem teto dentro de um repositório git. Ficam os 30 exports mais recentes,
// gzipados, MAIS o primeiro de todos — que é a testemunha do esquema e a única
// prova de como o cabeçalho era no dia em que o parser foi escrito. O sha256 de
// cada export fica no ledger para sempre, que é o que torna a poda reversível
// em auditoria: some o arquivo, nunca o registro de que ele existiu.
const EXPORTS_RETIDOS = 30;

// A identidade de saída, na forma que o contrato fixa. Escrita como cabeçalho
// (e não montada por concatenação) de propósito: é assim que
// tools/check-identidade-de-saida EXTRAI o valor e o julga. Um valor que o gate
// não consegue ler é um valor que ninguém fiscaliza.
const CABECALHO_CANONICO = {
  'User-Agent':
    'Mozilla/5.0 (compatible; WikijuridicaBot/1.0; +https://wikijuridica.com.br/bot/; coleta-de-citacao-ia)',
};

const COMANDO_DE_LOGIN = './tools/collect-bing-ai-citations --login';

// ────────────────────────────────────────────────────────────────── utilidades

const argv = process.argv.slice(2);
const tem = (flag) => argv.includes(flag);
const MODO_LOGIN = tem('--login');
const FORCAR = tem('--forcar');

function agora() {
  return new Date().toISOString();
}

function diaUTC() {
  return new Date().toISOString().slice(0, 10);
}

function log(texto) {
  process.stdout.write(texto + '\n');
}

function erro(texto) {
  process.stderr.write(texto + '\n');
}

/**
 * Encerra dizendo que NÃO MEDIU, com o motivo e o que fazer.
 *
 * Exit 2 e não 1: a convenção deste repositório separa "medi e está degradado"
 * (1, veredito de rotina, que a unit mascara) de "não consegui medir" (>=2,
 * instrumento quebrado, que precisa acordar o dono). Devolver 1 aqui faria o
 * alarme calar exatamente quando o instrumento parou.
 */
function naoMediu(motivo, comoResolver) {
  erro('NAO MEDIDO: ' + motivo);
  if (comoResolver) {
    erro('');
    erro(comoResolver);
  }
  process.exitCode = 2;
}

function leJSON(caminho, padrao) {
  try {
    return JSON.parse(readFileSync(caminho, 'utf8'));
  } catch {
    return padrao;
  }
}

function gravaLedger(registro) {
  mkdirSync(dirname(LEDGER), { recursive: true });
  appendFileSync(LEDGER, JSON.stringify(registro) + '\n', 'utf8');
}

function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

/**
 * Mantém os N exports mais recentes e SEMPRE o primeiro de todos.
 *
 * O primeiro é a testemunha do esquema: quando alguém perguntar "o parser foi
 * escrito contra qual cabeçalho?", a resposta tem de ser um arquivo, não uma
 * lembrança.
 */
function podaExports() {
  if (!existsSync(BRUTOS)) return [];
  const arquivos = readdirSync(BRUTOS)
    .filter((n) => n.endsWith('.csv.gz'))
    .sort();
  if (arquivos.length <= EXPORTS_RETIDOS + 1) return [];
  const primeiro = arquivos[0];
  const manter = new Set([primeiro, ...arquivos.slice(-EXPORTS_RETIDOS)]);
  const removidos = [];
  for (const nome of arquivos) {
    if (manter.has(nome)) continue;
    unlinkSync(join(BRUTOS, nome));
    removidos.push(nome);
  }
  return removidos;
}

// ───────────────────────────────────────────────── orçamento de requisições

/**
 * Conta as requisições que NÓS pedimos, e só elas.
 *
 * A distinção não é preciosismo: uma SPA dispara dezenas de XHR por navegação.
 * Contá-las no mesmo balde faria o teto estourar na primeira página e, pior,
 * faria o número "requisições ao Bing" que este projeto publica medir a
 * arquitetura da página deles em vez do nosso consumo.
 */
class Orcamento {
  constructor(teto) {
    this.teto = teto;
    this.gastas = 0;
  }

  gasta(oque) {
    if (this.gastas >= this.teto) {
      throw new Error(
        'teto de ' + this.teto + ' requisicoes deliberadas estourado antes de "' + oque + '"',
      );
    }
    this.gastas += 1;
  }
}

// ──────────────────────────────────────────────────────────────── navegador

async function abrirNavegador(perfil, { headless, uaCanonico }) {
  const opcoes = {
    channel: 'chrome',
    headless,
    viewport: { width: 1440, height: 900 },
    // O mesmo par do publicador social, pelo mesmo motivo medido: num perfil
    // recém-criado o pedido de notificação sobe como `role="alertdialog"` por
    // cima de tudo e INTERCEPTA O PONTEIRO — o Playwright diz "element is
    // visible, enabled and stable" e o clique bate no overlay até estourar.
    args: ['--disable-blink-features=AutomationControlled', '--disable-notifications'],
  };
  // RAMO 0 da medição de identidade: o contexto inteiro sai como WikijuridicaBot.
  // Fica atrás de uma variável de ambiente porque é o ramo que pode impedir o
  // painel de carregar, e a rotina diária não pode depender do ramo mais frágil.
  if (uaCanonico) {
    opcoes.userAgent = CABECALHO_CANONICO['User-Agent'];
  }
  const ctx = await chromium.launchPersistentContext(perfil, opcoes);
  await ctx.grantPermissions([]).catch(() => {});
  return ctx;
}

let contadorDeFotos = 0;
async function fotografar(page, nome) {
  mkdirSync(FOTOS, { recursive: true });
  contadorDeFotos += 1;
  const arquivo = join(
    FOTOS,
    diaUTC() + '-' + String(contadorDeFotos).padStart(2, '0') + '-' + nome + '.png',
  );
  await page.screenshot({ path: arquivo, fullPage: false }).catch(() => {});
  log('  foto: ' + arquivo);
  return arquivo;
}

/**
 * A sessão do titular está viva?
 *
 * Pela URL final, não por seletor: o Bing redireciona para `login.live.com`
 * quando não há sessão, e URL é o sinal que não depende de tradução, de teste
 * A/B nem de mudança de layout — que é o que quebra seletor.
 */
function pareceDeslogado(url) {
  const baixo = String(url).toLowerCase();
  return (
    baixo.includes('login.live.com') ||
    baixo.includes('login.microsoftonline.com') ||
    baixo.includes('/webmasters/about') ||
    baixo.includes('signin')
  );
}

// ─────────────────────────────────────────────────────────────── --login

async function fluxoDeLogin() {
  const { caminho: perfil } = perfilPronto();
  log('perfil do coletor : ' + perfil);
  log('');
  log('Abrindo o Bing Webmaster Tools para VOCÊ autenticar a conta Microsoft.');
  log('Nada é publicado, nada é enviado: o navegador só guarda a sessão no perfil');
  log('acima, que é exclusivo desta coleta e não toca o do publicador social.');
  log('');
  log('Quando o painel estiver aberto e o site já aparecer na lista, feche a');
  log('janela do navegador. A rotina diária passa a funcionar sozinha a partir daí.');
  const ctx = await abrirNavegador(perfil, { headless: false, uaCanonico: false });
  const page = ctx.pages()[0] ?? (await ctx.newPage());
  await page.goto(URL_ENTRADA, { waitUntil: 'domcontentloaded' });
  await ctx.waitForEvent('close', { timeout: 0 });
}

// ─────────────────────────────────────────────────────────────── coleta

async function coletar() {
  const estado = leJSON(ESTADO, {});
  const hoje = diaUTC();
  if (!FORCAR && estado.ultimo_dia_utc === hoje) {
    log('dia UTC ' + hoje + ' já coletado (' + (estado.ultimo_resultado ?? 'sem resultado') + ').');
    log('Nada a fazer. `--forcar` ignora o teto de 1 execução por dia.');
    return 0;
  }

  const { caminho: perfil, jaExistia } = perfilPronto();
  if (!jaExistia) {
    naoMediu(
      'esta máquina nunca autenticou a conta Microsoft: o perfil ' + perfil + ' acabou de ser criado.',
      'Não é defeito — é a estreia. O TITULAR roda UMA VEZ, na tela dele:\n' +
        '    ' + COMANDO_DE_LOGIN + '\n' +
        'Depois disso a rotina é automática e sem intervenção.',
    );
    return 2;
  }

  const orcamento = new Orcamento(TETO_REQUISICOES);
  const uaCanonicoNoContexto = process.env.WIKI_BING_IA_UA_CANONICO === '1';
  // HEADFUL POR PADRAO, e isto e' decisao medida pela ausencia de medicao.
  // `--headless` troca o User-Agent para `HeadlessChrome` e muda o fingerprint
  // que a Microsoft ve — e se a sessao do titular for recusada por causa disso,
  // o preco e' outro login dele, que e' a unica coisa nesta frente que nao se
  // automatiza. O `:99` existe justamente para o modo com janela nao custar
  // nada: e' um servidor X sem tela fisica. `--headless` fica como MEDICAO
  // pos-login, nunca como default; o publicador social, que funciona, tambem
  // roda com janela em `:99`.
  const ctx = await abrirNavegador(perfil, {
    headless: tem('--headless'),
    uaCanonico: uaCanonicoNoContexto,
  });

  // O que o PAINEL pediu por conta própria. É daqui que sai o token, e é daqui
  // que sai a prova de qual é a rota de exportação — nenhum dos dois se inventa.
  const observadas = [];
  let token = null;
  let exportObservado = null;

  const registraRequisicao = (req) => {
    const url = req.url();
    if (!url.includes('bing.com/webmasters/')) return;
    const cabecalhos = req.headers();
    const csrf = cabecalhos['x-csrf-token'] ?? cabecalhos['X-CSRF-Token'] ?? null;
    if (csrf && !token) token = csrf;
    let corpo = null;
    try {
      corpo = req.postData();
    } catch {
      corpo = null;
    }
    const registro = {
      metodo: req.method(),
      url,
      tem_csrf: Boolean(csrf),
      // O `content-type` do PAINEL, nao um que a gente suponha. Forcar
      // `application/json` e fazer `JSON.parse` no corpo seria a ultima
      // suposicao de esquema sobrevivente num desenho que existe para deixar o
      // painel falar: se o pedido dele for form-encoded, o parse quebra e o
      // coletor sai com 2 por um defeito que inventamos.
      content_type: cabecalhos['content-type'] ?? null,
      corpo: corpo ? corpo.slice(0, 2000) : null,
    };
    observadas.push(registro);
    if (
      req.method() === 'POST' &&
      /aiperformance|citationstats|\/export/i.test(url) &&
      !exportObservado
    ) {
      exportObservado = registro;
    }
  };

  try {
    const page = ctx.pages()[0] ?? (await ctx.newPage());
    page.on('request', registraRequisicao);

    orcamento.gasta('abrir o painel');
    await page.goto(URL_PAINEL_IA + '?siteUrl=' + encodeURIComponent(SITE), {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    await page.waitForTimeout(6000);
    await fotografar(page, 'painel-ia');

    const urlFinal = page.url();
    log('URL final         : ' + urlFinal);
    if (pareceDeslogado(urlFinal)) {
      naoMediu(
        'a sessão da conta Microsoft não está viva (a navegação terminou em ' + urlFinal + ').',
        'O TITULAR roda UMA VEZ, na tela dele:\n' +
          '    ' + COMANDO_DE_LOGIN + '\n' +
          'Não é cadastro novo, não é credencial nova, não é aprovação: é a conta dele,\n' +
          'num navegador que o projeto já opera. Depois disso a rotina é automática.',
      );
      return 2;
    }

    // Clicar no controle de exportação é o que faz o PAINEL revelar a rota e o
    // formato do pedido. Se o controle não existir com este rótulo, não se
    // insiste por tentativa: fotografa-se e registra-se o que foi visto.
    const rotulos = [/^Exportar$/i, /^Export$/i, /^Baixar$/i, /^Download$/i, /exportar/i];
    let clicou = false;
    for (const rotulo of rotulos) {
      const alvo = page.getByRole('button', { name: rotulo }).first();
      if ((await alvo.count().catch(() => 0)) > 0) {
        await alvo.click({ timeout: 5000 }).catch(() => {});
        clicou = true;
        break;
      }
    }
    await page.waitForTimeout(4000);
    await fotografar(page, clicou ? 'apos-exportar' : 'sem-controle-de-exportacao');

    if (!token) {
      naoMediu(
        'nenhuma requisição do painel trouxe `x-csrf-token` em ' +
          observadas.length +
          ' requisição(ões) observada(s): sem o token não há como repetir a exportação.',
        'As fotos estão em ' + FOTOS + ' e as requisições observadas foram gravadas no\n' +
          'ledger com tipo `citacao_ia_reconhecimento`. A próxima execução parte delas.',
      );
      gravaLedger({
        tipo: 'citacao_ia_reconhecimento',
        schema: SCHEMA,
        site: SITE,
        coletado_em: agora(),
        url_final: urlFinal,
        clicou_exportar: clicou,
        requisicoes_observadas: observadas.slice(0, 40),
        token_colhido: false,
        motivo: 'sem x-csrf-token em nenhuma requisicao do painel',
      });
      return 2;
    }

    if (!exportObservado) {
      naoMediu(
        'o painel não disparou nenhuma requisição de exportação: a rota de export ' +
          'continua NÃO OBSERVADA, e o caminho relatado não está provado.',
        'O que foi observado ficou no ledger (`citacao_ia_reconhecimento`), com as URLs e os\n' +
          'corpos. Leia-o junto com as fotos em ' + FOTOS + ' antes de supor uma rota:\n' +
          'quatro POSTs a caminhos diferentes já devolveram a MESMA resposta de anti-forgery,\n' +
          'então "400" ali não distingue rota que existe de rota que não existe.',
      );
      gravaLedger({
        tipo: 'citacao_ia_reconhecimento',
        schema: SCHEMA,
        site: SITE,
        coletado_em: agora(),
        url_final: urlFinal,
        clicou_exportar: clicou,
        requisicoes_observadas: observadas.slice(0, 40),
        token_colhido: true,
        motivo: 'nenhuma requisicao de exportacao observada',
      });
      return 2;
    }

    // ── a exportação, repetida com o token DESTA execução ────────────────────
    //
    // RAMO 1 primeiro: o UA canônico injetado na requisição que colhe o dado.
    // RAMO 2 só se o ramo 1 for recusado, e o resultado dos dois vai para o
    // ledger — é assim que a exceção de identidade deixa de ser proposta e vira
    // número.
    const tentativas = [
      { ramo: 'ramo_1_ua_canonico', cabecalhos: { ...CABECALHO_CANONICO, 'x-csrf-token': token } },
      { ramo: 'ramo_2_ua_do_navegador', cabecalhos: { 'x-csrf-token': token } },
    ];

    let resultado = null;
    for (const tentativa of tentativas) {
      orcamento.gasta('exportacao ' + tentativa.ramo);
      const cabecalhosDoPedido = { ...tentativa.cabecalhos };
      if (exportObservado.content_type) {
        cabecalhosDoPedido['Content-Type'] = exportObservado.content_type;
      }
      const resposta = await ctx.request.post(exportObservado.url, {
        headers: cabecalhosDoPedido,
        // CORPO CRU, byte a byte o que o painel mandou. Reserializar exigiria
        // saber o formato, e saber o formato e' exatamente o que esta execucao
        // esta descobrindo.
        data: exportObservado.corpo ?? '',
        timeout: 60000,
      });
      const corpo = Buffer.from(await resposta.body());
      log(tentativa.ramo + ' → HTTP ' + resposta.status() + ', ' + corpo.length + ' bytes');
      resultado = {
        ramo: tentativa.ramo,
        status: resposta.status(),
        bytes: corpo.length,
        corpo,
        inicio_do_corpo: corpo.slice(0, 400).toString('utf8'),
      };
      if (resposta.ok() && corpo.length > 0) break;
    }

    if (!resultado || resultado.status >= 400 || resultado.bytes === 0) {
      gravaLedger({
        tipo: 'citacao_ia_export',
        schema: SCHEMA,
        site: SITE,
        coletado_em: agora(),
        ok: false,
        ramo_de_identidade: resultado ? resultado.ramo : null,
        http_status: resultado ? resultado.status : null,
        bytes: resultado ? resultado.bytes : 0,
        inicio_do_corpo: resultado ? resultado.inicio_do_corpo : null,
        url_de_exportacao: exportObservado.url,
        requisicoes_deliberadas: orcamento.gastas,
        requisicoes_do_painel: observadas.length,
      });
      naoMediu(
        'a exportação foi recusada nos dois ramos de identidade (último: HTTP ' +
          (resultado ? resultado.status : 'sem resposta') + ').',
        'O status e o começo do corpo ficaram no ledger. Leia-os antes de mudar o pedido.',
      );
      return 2;
    }

    // ── FASE 1: preserva o cru e descreve o que veio, sem interpretar ────────
    mkdirSync(BRUTOS, { recursive: true });
    const nomeBruto = 'export-' + hoje + '.csv.gz';
    const caminhoBruto = join(BRUTOS, nomeBruto);
    writeFileSync(caminhoBruto, gzipSync(resultado.corpo));
    const texto = resultado.corpo.toString('utf8');
    const linhas = texto.split('\n').filter((l) => l.trim() !== '');
    const cabecalhoCSV = linhas.length > 0 ? linhas[0] : null;
    const removidos = podaExports();

    gravaLedger({
      tipo: 'citacao_ia_export',
      schema: SCHEMA,
      site: SITE,
      coletado_em: agora(),
      ok: true,
      // O RAMO DE IDENTIDADE QUE O BING ACEITOU. É este campo que transforma a
      // exceção nomeada em `wikijuridicabot.NavegadorRealDoTitular` de proposta
      // em fato — e o motivo daquela entrada é reescrito com o número daqui.
      ramo_de_identidade: resultado.ramo,
      http_status: resultado.status,
      url_de_exportacao: exportObservado.url,
      content_type_do_pedido: exportObservado.content_type,
      corpo_do_pedido: exportObservado.corpo,
      bytes: resultado.bytes,
      raw_sha256: sha256(resultado.corpo),
      arquivo_bruto: 'data/ops/bing_ai_citations/' + nomeBruto,
      linhas: linhas.length,
      // O CABEÇALHO VERBATIM. É a única coisa que a fase 1 precisa entregar ao
      // humano, e é o que autoriza a fase 2 a existir: o parser dos campos só se
      // escreve DEPOIS de alguém ler esta string. Antes disso, seria esquema
      // inventado passando por medição.
      cabecalho_csv: cabecalhoCSV,
      parser_de_campos: 'ausente_por_desenho',
      motivo_do_parser_ausente:
        'FASE 1: o esquema do CSV nunca foi visto por este projeto. O parser e o bloco ' +
        '`citacao_ia_diaria` se escrevem lendo `cabecalho_csv` desta linha.',
      requisicoes_deliberadas: orcamento.gastas,
      requisicoes_do_painel: observadas.length,
      exports_podados: removidos,
    });

    log('');
    log('=== EXPORT CAPTURADO (fase 1) ===');
    log('ramo de identidade: ' + resultado.ramo);
    log('bytes             : ' + resultado.bytes);
    log('linhas            : ' + linhas.length);
    log('sha256            : ' + sha256(resultado.corpo));
    log('cabecalho do CSV  : ' + cabecalhoCSV);
    log('bruto preservado  : ' + caminhoBruto);
    log('');
    log('FASE 2 — o parser dos campos e o bloco `citacao_ia_diaria` se escrevem A PARTIR');
    log('do cabeçalho acima. Escrevê-los antes seria inventar esquema.');

    writeFileSync(
      ESTADO,
      JSON.stringify(
        {
          ultimo_dia_utc: hoje,
          ultimo_resultado: 'export capturado',
          ramo_de_identidade: resultado.ramo,
          url_de_exportacao: exportObservado.url,
          atualizado_em: agora(),
        },
        null,
        2,
      ) + '\n',
      'utf8',
    );
    return 0;
  } finally {
    await ctx.close().catch(() => {});
  }
}

// ──────────────────────────────────────────────────────────────────── main

try {
  if (MODO_LOGIN) {
    await fluxoDeLogin();
    log('sessão guardada no perfil. A rotina diária pode ser habilitada agora.');
    process.exit(0);
  }
  const codigo = await coletar();
  process.exit(codigo);
} catch (falha) {
  // TODA EXCEÇÃO NÃO TRATADA É "NÃO MEDIU", nunca "medi e está tudo bem". É o
  // mesmo raciocínio de tools/lib/saida_de_medidor.py do lado Python: o
  // interpretador sai com 1 por conta própria, a unit mascara o 1 de propósito,
  // e o instrumento quebrado ficaria indistinguível do instrumento que mediu.
  erro('NAO MEDIDO: exceção não tratada no coletor.');
  erro(falha && falha.stack ? falha.stack : String(falha));
  process.exit(2);
}
