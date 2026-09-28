// Prova de navegador: o fragmento percent-encoded em UTF-8 (%C2%A7) casa o id
// `art206§3` de um documento servido em latin-1?
//
// O documento e' a COPIA LOCAL baixada pelo gerador (byte a byte a mesma), aberta
// por file://. A correspondencia de fragmento e' propriedade do NAVEGADOR, nao do
// servidor, entao o file:// prova o mesmo e nao manda navegador nenhum para fora
// (o CLAUDE.md §11 proibe sair como navegador).
import { chromium } from 'playwright-core'
import process from 'node:process'

const arquivo = process.argv[2]
const casos = process.argv.slice(3)
if (!arquivo || casos.length === 0) {
  console.error('uso: prova_fragmento.mjs <arquivo.html> <id> [id...]')
  process.exit(2)
}

const navegador = await chromium.launch({ headless: true, channel: 'chrome' })
const pagina = await navegador.newPage()
const resultados = []
for (const id of casos) {
  const fragmento = encodeURIComponent(id)
  await pagina.goto(`file://${arquivo}#${fragmento}`, { waitUntil: 'load' })
  const medido = await pagina.evaluate(() => ({
    // O Planalto ancora com `<a name="...">` sem `id`. Em DOM, `el.id` de um
    // elemento sem o atributo e STRING VAZIA, nao null — entao `??` nao cai no
    // `name` e a medicao devolveria "" para tudo, inclusive para o caso que
    // casou. O `||` e' o operador certo aqui.
    alvo: (() => { const el = document.querySelector(':target'); return el ? (el.id || el.getAttribute('name') || '') : null })(),
    charset: document.characterSet,
    rolagem: Math.round(window.scrollY),
  }))
  resultados.push({ id, fragmento, ...medido })
  console.log(`${id}  ->  #${fragmento}  :target=${JSON.stringify(medido.alvo)}  charset=${medido.charset}  scrollY=${medido.rolagem}`)
}
await navegador.close()
const ok = resultados.filter((r) => r.alvo === r.id).length
console.log(`\ncasou: ${ok}/${resultados.length}`)
process.exit(ok === resultados.length ? 0 : 1)
