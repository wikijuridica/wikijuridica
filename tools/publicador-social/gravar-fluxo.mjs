#!/usr/bin/env node
/**
 * gravar-fluxo.mjs — abre o navegador do publicador e GRAVA cada clique que o
 * titular der, para que os seletores saiam de medição e não de tentativa.
 *
 * POR QUE. Descobrir seletor por chute revela um defeito por execução: foram
 * três rodadas (overlay, nome do campo, nome do botão) e a terceira mostrou que
 * eu clicava no modal errado o tempo todo. Aqui o caminho se inverte — quem
 * conhece o fluxo é o humano, e a máquina só anota o que ele fez.
 *
 * USO
 *   node gravar-fluxo.mjs              grava no Facebook (padrão)
 *   node gravar-fluxo.mjs instagram
 *
 * Faça o fluxo INTEIRO até o post ir ao ar e feche o navegador. Cada clique vai
 * para cliques.jsonl com aria-label, texto, papel e um seletor derivado.
 *
 * NÃO PUBLICA NADA SOZINHO: quem clica é o titular. A ferramenta só observa.
 */
import { chromium } from 'playwright-core';
import { appendFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { perfilPronto } from './perfil.mjs';

const AQUI = dirname(fileURLToPath(import.meta.url));
// O perfil mora FORA da arvore do repositorio: ele guarda Cookies e Login
// Data das sessoes autenticadas, e `.gitignore` nao impede que credencial
// viva viaje em copia, backup ou varredura. O porque completo, com a
// medicao, esta em perfil.mjs.
const PERFIL = perfilPronto(AQUI);
const SAIDA = join(AQUI, 'cliques.jsonl');

const DESTINOS = {
  facebook: 'https://www.facebook.com/wikijuridica',
  instagram: 'https://www.instagram.com/',
  linkedin: 'https://www.linkedin.com/feed/',
};
const rede = process.argv[2] || 'facebook';
const destino = DESTINOS[rede] ?? DESTINOS.facebook;

writeFileSync(SAIDA, '', 'utf8');

const ctx = await chromium.launchPersistentContext(PERFIL, {
  channel: 'chrome',
  headless: false,
  viewport: { width: 1440, height: 900 },
  args: ['--disable-blink-features=AutomationControlled', '--disable-notifications'],
});
await ctx.grantPermissions([]).catch(() => {});

// O binding roda no Node e grava em disco; o listener injetado o chama.
await ctx.exposeBinding('__anotarClique', (_fonte, dados) => {
  appendFileSync(SAIDA, JSON.stringify(dados) + '\n', 'utf8');
  const rotulo = dados.aria || dados.texto || `<${dados.tag}>`;
  console.log(`  clique #${dados.n}: "${rotulo}"  role=${dados.role || '-'}`);
});

// addInitScript e não um listener numa página só: o Facebook troca de documento
// e reabre modais, e um listener comum morreria na primeira navegação.
await ctx.addInitScript(() => {
  let n = 0;
  const descrever = (el) => {
    // Sobe até o ancestral clicável mais próximo: o clique costuma cair num
    // <span> interno, e quem responde por ele é o botão que o contém.
    let alvo = el;
    for (let i = 0; i < 6 && alvo; i++) {
      const r = alvo.getAttribute?.('role');
      if (r === 'button' || r === 'link' || alvo.tagName === 'BUTTON' || alvo.tagName === 'A') break;
      alvo = alvo.parentElement;
    }
    alvo = alvo || el;
    const modais = [...document.querySelectorAll('[role=dialog]')];
    return {
      n: ++n,
      tag: alvo.tagName,
      role: alvo.getAttribute('role') || '',
      aria: (alvo.getAttribute('aria-label') || '').slice(0, 80),
      texto: (alvo.innerText || '').trim().slice(0, 80),
      testid: alvo.getAttribute('data-testid') || '',
      // Em qual dos diálogos empilhados o clique caiu — o Facebook mantém o
      // composer e o editor de foto abertos ao mesmo tempo.
      dentroDeModal: modais.findIndex((m) => m.contains(alvo)),
      totalModais: modais.length,
      classe: (alvo.className || '').toString().slice(0, 60),
      url: location.pathname,
    };
  };
  // capture: true garante que anotamos ANTES de o site cancelar o evento.
  addEventListener('click', (ev) => {
    try { window.__anotarClique(descrever(ev.target)); } catch {}
  }, { capture: true });
});

const page = ctx.pages()[0] ?? (await ctx.newPage());
await page.goto(destino, { waitUntil: 'domcontentloaded' });

console.log(`\nGRAVANDO cliques em ${rede}.`);
console.log('Faça a publicação INTEIRA, do começo até o post no ar.');
console.log('Cada clique aparece aqui e vai para cliques.jsonl.');
console.log('Quando terminar, FECHE a janela do navegador.\n');

await ctx.waitForEvent('close', { timeout: 0 });
console.log(`\nGravação encerrada. Registro em ${SAIDA}`);
