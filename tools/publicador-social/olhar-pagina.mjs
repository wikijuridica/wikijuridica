#!/usr/bin/env node
/**
 * olhar-pagina.mjs — abre o fluxo de publicação e tira SCREENSHOT DA PÁGINA,
 * para que o agente veja o que o seletor não alcança.
 *
 * POR QUE ISTO, E NÃO CONTROLAR A TELA DO SERVIDOR. A tela é o notebook do dono
 * (Lenovo IdeaPad, painel interno, bateria — medido), com o trabalho dele
 * aberto: terminais, uma VM Windows, o gerenciador de tarefas. Um agente
 * movendo o mouse ali disputa o cursor com ele, e `xdotool type` sem --window
 * digita no que estiver focado — uma legenda de post cairia dentro de um shell.
 *
 * O Playwright dá a MESMA capacidade sem nenhum desses riscos:
 *   page.screenshot()      -> o agente vê a página, como veria a tela
 *   page.mouse.click(x, y) -> clica por coordenada, sem depender de seletor
 *   locator.boundingBox()  -> converte elemento em coordenada quando o DOM ajuda
 *
 * E roda no Chrome do perfil dedicado, então não toca na sessão do dono, não
 * rouba foco e funciona com a tela bloqueada. Ver a página resolve o problema
 * real (o seletor que não acha o botão); ver a TELA resolveria o mesmo problema
 * trazendo junto o risco de clicar no terminal ao lado.
 *
 * USO
 *   node olhar-pagina.mjs                 percorre o fluxo e fotografa cada etapa
 *   node olhar-pagina.mjs --etapa 3       para na etapa e mantém o navegador aberto
 */
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { perfilPronto } from './perfil.mjs';

const AQUI = dirname(fileURLToPath(import.meta.url));
// O perfil mora FORA da arvore do repositorio: ele guarda Cookies e Login
// Data das sessoes autenticadas, e `.gitignore` nao impede que credencial
// viva viaje em copia, backup ou varredura. O porque completo, com a
// medicao, esta em perfil.mjs.
const PERFIL = perfilPronto(AQUI);
const FOTOS = join(AQUI, '../../.agents/runtime/tela/fluxo-facebook');
const ARTE = join(AQUI, '../../.agents/runtime/artes-perfis-20260827/01-familia.png');

mkdirSync(FOTOS, { recursive: true });

const ctx = await chromium.launchPersistentContext(PERFIL, {
  channel: 'chrome',
  headless: false,
  viewport: { width: 1280, height: 900 },
  args: ['--disable-blink-features=AutomationControlled', '--disable-notifications'],
});
await ctx.grantPermissions([]).catch(() => {});
const page = ctx.pages()[0] ?? (await ctx.newPage());

let n = 0;
async function fotografar(nome) {
  const arquivo = join(FOTOS, `${String(++n).padStart(2, '0')}-${nome}.png`);
  await page.screenshot({ path: arquivo });
  console.log(`  foto ${n}: ${arquivo}`);
}

await page.goto('https://www.facebook.com/wikijuridica', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4000);
await fotografar('perfil');

await page.getByText(/No que você está pensando/i).first().click();
await page.locator('[role=dialog]').first().waitFor({ state: 'visible', timeout: 20000 });
await page.waitForTimeout(2500);
await fotografar('composer-aberto');

const [chooser] = await Promise.all([
  page.waitForEvent('filechooser', { timeout: 20000 }),
  page.getByRole('button', { name: /^Foto\/vídeo$/i }).first().click(),
]);
await chooser.setFiles(ARTE);
await page.waitForTimeout(5000);
await fotografar('com-imagem');

const campo = page.locator('[contenteditable="true"][role="textbox"]').last();
await campo.click();
await campo.type('Diagnóstico visual — não publicar.', { delay: 10 });
await page.waitForTimeout(2000);
await fotografar('com-texto');

const avancar = page.getByRole('button', { name: /^Avançar$/i }).first();
if (await avancar.isVisible().catch(() => false)) {
  await avancar.click();
  await page.waitForTimeout(4000);
  await fotografar('apos-avancar-AQUI-ESTA-O-BOTAO-FINAL');

  // Rola o modal até o fim: o botão final costuma ficar no rodapé, fora da
  // viewport, e foi por isso que a busca por texto não o achou.
  await page.mouse.wheel(0, 1500);
  await page.waitForTimeout(1500);
  await fotografar('apos-avancar-rolado');
}

console.log('\nFotos em', FOTOS);
console.log('NADA foi publicado. Fechando.');
await ctx.close();
