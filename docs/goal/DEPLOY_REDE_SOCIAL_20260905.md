# Deploy de 2026-09-05 — navegação da rede social e âncora no acervo

Preparado por medição própria. Cada passo diz **por que** está nessa posição:
ordem errada aqui já custou 504 em laço e repopulação do Tiered Cache com
conteúdo velho, as duas medidas neste repositório.

---

## 1. O que este deploy leva

| Mudança | Alcance | Efeito no `served_sha256` |
|---|---|---|
| Navegação do cabeçalho derivada do multiplexador | todas as telas de `/redesocial/` | rota dinâmica: não há `public/`, não há re-datação |
| Navegação também na gêmea Markdown | idem | idem |
| Perfil público criado no cadastro | `cmd/social` | idem |
| Nó JSON-LD `QAPage` nas threads indexáveis | idem | idem |
| **Âncora `/redesocial/` na home do portal** | 1 página | **muda** — e a mudança é verdadeira |
| **Âncora `/redesocial/` nos hubs de área** | ~43 hubs + fatias | **muda** — verdadeira |
| Âncora no bloco de relacionados | 10.141 páginas | **não muda** — cai dentro do trecho neutralizado |

### Por que a âncora do acervo não re-data as 10.141

`tools/generate-page-content-revision:309` neutraliza
`<section aria-labelledby="conteudos-relacionados".*?</section>` para `@NAV@`
antes de hashear. `renderRelatedContent` emite a âncora **entre `</ul>` e
`</section>`**, dentro do trecho neutralizado. Medido: `internal/render` verde,
`bloco_max` permanece 1.307 B e a projeção no teto editorial de 8 links vai a
1.456 B, contra teto de 1.800 B do `check-internal-link-block`.

A home e os hubs **não têm** esse bloco — são hub, não spoke. Ali a âncora muda
o hash e re-data a página, o que é correto: elas mudaram de fato. São ~228
páginas, não dez mil.

---

## 2. A decisão de `--ressemear`, e ela é NÃO

A matriz do contrato (§6 do `CLAUDE.md`) manda `--ressemear` para "markup, CSS,
atributo servido" e **proíbe** para "malha de links / bloco de relacionados",
porque usá-lo suprimiria a re-datação legítima do JSON-LD.

Este deploy é do segundo caso. Usar `--ressemear` re-dataria as 10.141 páginas
cujo HTML servido **não mudou** — re-datação fabricada, que faz o sitemap
reanunciar o acervo inteiro ao Googlebot como conteúdo novo. As ~228 que
mudaram de verdade re-datam sozinhas, pelo hash.

```
./tools/deploy-publico            # SEM --ressemear
```

---

## 3. Purga: ampla e manual, e ela é obrigatória

A mesma linha da matriz que proíbe `--ressemear` **exige** purga ampla manual
para mudança de malha de links. O motivo é medido: `--purge-targets` deriva do
hash neutralizado, e como o hash das 10.141 não muda, ele devolveria **zero
rotas** — a borda serviria o acervo sem âncora por até 7 dias (`s-maxage=604800`).

**Se o deploy imprimir `purgando tudo`, NÃO purgue de novo**: ele detectou
mudança de camada sozinho, e purgar duas vezes joga fora ~870 s de aquecimento.

```
./tools/purge-edge-cache          # só se o deploy NÃO tiver purgado tudo
```

---

## 4. Ordem, e cada inversão dela tem um incidente medido atrás

```
1. commit                      # o índice compila; nada entra em public/ sem estar versionado
2. ./tools/deploy-publico      # regenera public/ com a âncora na home e nos hubs
3. ./tools/deploy-binario-go   # binário social: navegação, perfil, JSON-LD
4. invalidar a origem          # warm-origin-cache
5. purgar a borda              # só depois de 4
6. aquecer
```

**Por que o binário depois do `public/`**: são artefatos independentes, mas
`deploy-publico` recarrega o nginx (linha 657) **antes** da troca do binário
social (686-690) — há uma janela em que o nginx serve a config nova contra o
8091 antigo. Rodar o binário logo em seguida a fecha.

**Por que purgar a borda só depois de invalidar a origem**: medido em
2026-09-05 — purgar antes repopula o Tiered Cache com o conteúdo VELHO (`HIT`,
`age: 0`, campos = 0, cinco vezes seguidas).

**O binário social vai por `deploy-binario-go`**, nunca à mão: a ordem
binário → socket → serviço existe porque socket `Type=notify` ativado com
binário que ignora `LISTEN_FDS` entra em laço de `EADDRINUSE` a cada 5 s com a
porta em LISTEN, servindo 504.

---

## 5. Verificação depois, e o que cada uma responde

```
./tools/check-http-smoke                       # acervo, canal de máquina e 8091
curl -sI -A 'wikijuridica-superficie-probe/1.0' -H 'X-Warming-Request: true' \
     https://wikijuridica.com.br/redesocial/   # menu servido pela borda
./tools/check-csp-style-hashes                 # a folha do acervo contra public/ novo
```

Na home e num hub, o `<p><a href="/redesocial/">` tem de aparecer. Em
`/redesocial/`, o cabeçalho tem de trazer Perguntas, Perguntar, Consultar a lei,
Conferir citação, Entrar e Criar conta — e **não** Cursos, enquanto
`content/cursos.json` não declarar curso.

`edge_cache_coverage` e o aquecimento vão registrar a borda fria logo depois da
purga. **É esperado, não é defeito.**

---

## 6. O que este deploy NÃO corrige — e uma leitura que corrige o gate

`./tools/check-internal-link-block` reprova hoje com **478 pares acima do limiar**
(contra baseline de 106) e **43 páginas sem ponte cross-área** (contra 23). Os
exemplos são de jurisprudência: `/jurisprudencia/stf-adi-6553/` e
`/stf-adi-7467/` chegam a Jaccard **1,0**.

**Não é regressão deste deploy**, e a prova está no próprio relatório:
`bloco_max=1307B` é o valor de ANTES da âncora, porque o gate mede `public/`,
que ainda não a tem. E `deploy-publico` **não** executa esse gate — conferido
por leitura da ferramenta —, então ele não bloqueia a publicação.

### E o rótulo "doorway" está errado, medido na implementação

`tools/measure-link-graph:187` — `pares_doorway` compara **os conjuntos de
vizinhos do bloco de links**, não o corpo das páginas:

```python
por_area[area_de(rota)][rota] = set(destinos)
```

Jaccard 1,0 ali significa "estas duas páginas apontam para os mesmos vizinhos",
e não "estas duas páginas têm o mesmo conteúdo". Doorway, na definição que os
buscadores publicam e que o gate invoca pelo nome, é sobre **conteúdo**
duplicado criado para capturar busca — coisa que este detector não mede.

Duas ADI do STF da mesma área citarem os mesmos precedentes vizinhos é a malha
temática **funcionando**: é o comportamento certo, não o defeito. Ordem do dono,
2026-09-05: peça de jurisprudência é curta e padronizada por natureza, e só há
bug quando as páginas envolvidas são **densas** — aí o bloco idêntico denuncia
malha preguiçosa, porque havia corpo próprio suficiente para gerar vizinhança
distinta.

Medido agora, texto extraído do HTML publicado: `stf-adi-6553` 10.057 B,
`stf-adi-7467` 9.453 B, `stf-adi-7373` 11.608 B, contra 12.064 B de
`/familia/abandono-afetivo-indenizacao/`. Estão na mesma ordem de grandeza — mas
o número inclui cabeçalho, rodapé e o próprio bloco de links, então ele **não**
decide sozinho a questão da densidade editorial.

**A correção certa, e é de frente própria, não deste deploy:** o detector precisa
condicionar o achado à densidade do corpo editorial (não do HTML inteiro) das
duas páginas do par, e o rótulo precisa dizer o que ele mede — "vizinhança
idêntica na mesma área". Um gate que reprova o comportamento correto de um
conjunto inteiro de rotas é um gate que ensina a ser ignorado, e é o oitavo caso
desta sessão de detector cujo nome promete mais do que ele mede.
