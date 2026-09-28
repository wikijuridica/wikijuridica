#!/usr/bin/env node
/**
 * diagnosticar.mjs — percorre o fluxo de publicação e IMPRIME o que existe na
 * tela, sem publicar nada.
 *
 * Existe porque corrigir seletor por tentativa é um loop caro: cada chute custa
 * uma execução inteira do navegador e revela UM defeito por vez. Foram três
 * assim (overlay de notificação, nome do campo de texto, nome do botão) antes
 * de eu parar e escrever isto. Medir o DOM real de uma vez responde todas.
 *
 *   node diagnosticar.mjs facebook
 */
import { chromium } from 'playwright-core';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { perfilPronto } from './perfil.mjs';

const AQUI = dirname(fileURLToPath(import.meta.url));
// O perfil mora FORA da arvore do repositorio: ele guarda Cookies e Login
// Data das sessoes autenticadas, e `.gitignore` nao impede que credencial
// viva viaje em copia, backup ou varredura. O porque completo, com a
// medicao, esta em perfil.mjs.
const PERFIL = perfilPronto(AQUI);
const ARTE = join(AQUI, '../../.agents/runtime/artes-perfis-20260827/01-familia.png');

async function botoesVisiveis(page, titulo) {
  const lista = await page.evaluate(() => {
    const dentro = (el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    };
    // SO o que esta dentro do modal: a pagina de perfil por tras tem dezenas de
    // botoes ("Adicionar aos amigos", recomendacoes) que afogam o que importa.
    // TODOS os dialogos: o Facebook empilha o composer e o editor de foto, e
    // pegar so o ultimo (.pop()) mostrava um modal com um botao so.
    const modais = [...document.querySelectorAll('[role=dialog]')];
    const alvo = modais.length ? modais : [document];
    return alvo.flatMap((m, i) => [...m.querySelectorAll('[role=button], button, [role=link]')]
      .filter(dentro)
      .map(b => Object.assign(b, { __modal: i })))
      .map((b) => ({
        modal: b.__modal,
        txt: (b.innerText || '').trim().slice(0, 40),
        aria: (b.getAttribute('aria-label') || '').slice(0, 40),
        disabled: b.getAttribute('aria-disabled') || '',
      }))
      .filter((b) => b.txt || b.aria)
      .slice(0, 60);
  });
  console.log(`\n===== ${titulo} =====`);
  for (const b of lista) console.log(`  [modal ${b.modal}] "${b.txt}"${b.aria ? `  [aria: ${b.aria}]` : ''}${b.disabled ? '  DISABLED' : ''}`);
}

const ctx = await chromium.launchPersistentContext(PERFIL, {
  channel: 'chrome', headless: false, viewport: { width: 1440, height: 900 },
  args: ['--disable-blink-features=AutomationControlled', '--disable-notifications'],
});
const page = ctx.pages()[0] ?? (await ctx.newPage());

await page.goto('https://www.facebook.com/wikijuridica', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(4000);
await page.getByText(/No que você está pensando/i).first().click();
// Espera o modal EXISTIR antes de medir. Sem isto a captura pega a pagina de
// perfil por tras e o relatorio inteiro descreve a tela errada.
await page.locator('[role=dialog]').first().waitFor({ state: 'visible', timeout: 20000 });
await page.waitForTimeout(2500);
await botoesVisiveis(page, '1. composer aberto, ANTES da imagem');

const [chooser] = await Promise.all([
  page.waitForEvent('filechooser', { timeout: 20000 }),
  page.getByRole('button', { name: /^Foto\/vídeo$/i }).first().click(),
]);
await chooser.setFiles(ARTE);
await page.waitForTimeout(5000);
await botoesVisiveis(page, '2. DEPOIS da imagem subir');

const campo = page.locator('[contenteditable="true"][role="textbox"]').last();
await campo.click();
await campo.type('Teste de diagnóstico — este texto NÃO será publicado.', { delay: 10 });
await page.waitForTimeout(2000);
await botoesVisiveis(page, '3. DEPOIS de digitar a legenda (aqui mora o botão de publicar)');

// PASSO 4: o "Avançar" leva a uma tela seguinte, e e la que mora o botao final.
const avancar = page.getByRole('button', { name: /^Avançar$/i }).first();
if (await avancar.isVisible().catch(() => false)) {
  await avancar.click();
  await page.waitForTimeout(4000);
  await botoesVisiveis(page, '4. DEPOIS de Avançar — o botão final está AQUI');
} else {
  console.log('\n(sem botão Avançar nesta tela)');
}

// ROLA o modal ate o fim: a tela de opcoes e mais alta que a viewport e o
// botao final fica no rodape dela.
await page.evaluate(() => {
  for (const d of document.querySelectorAll('[role=dialog]')) {
    d.scrollTop = d.scrollHeight;
    for (const el of d.querySelectorAll('*')) {
      if (el.scrollHeight > el.clientHeight + 40) el.scrollTop = el.scrollHeight;
    }
  }
});
await page.mouse.wheel(0, 1200);
await page.waitForTimeout(2500);
await botoesVisiveis(page, '4b. depois de ROLAR o modal de opções');

// Busca AMPLA pelo botao final: qualquer elemento clicavel, em qualquer lugar
// da pagina, cujo texto ou aria-label soe como publicacao.
const finais = await page.evaluate(() => {
  const alvo = /^(Publicar|Publique agora|Compartilhar|Concluir|Post|Share)$/i;
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width < 12 || r.height < 12) continue;
    const t = (el.innerText || '').trim();
    const a = (el.getAttribute('aria-label') || '').trim();
    if ((alvo.test(t) && t.length < 30) || alvo.test(a)) {
      out.push({ tag: el.tagName, role: el.getAttribute('role') || '', txt: t.slice(0,30), aria: a.slice(0,30),
                 y: Math.round(r.top), clicavel: el.getAttribute('role') === 'button' || el.tagName === 'BUTTON' });
    }
  }
  return out.slice(0, 20);
});
console.log('\n===== 5. BUSCA AMPLA pelo botão final =====');
for (const f of finais) console.log(`  <${f.tag} role=${f.role||'-'}> "${f.txt}" [aria: ${f.aria}] y=${f.y} clicavel=${f.clicavel}`);

console.log('\n(nada publicado — fechando)');
await ctx.close();
