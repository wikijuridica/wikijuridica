---
name: invalidar-cache-por-formula-nao-mede-ausencia
description: Ao invalidar cache (nginx wj_dyn) ou qualquer store endereçado por hash, SELECIONE lendo o que está gravado e CONFIRA a ausência depois de remover — derivar o nome do objeto por fórmula alcança 1 de 2 a 3
metadata:
  type: feedback
---

Ferramenta que invalida cache **não deriva o nome do objeto de uma fórmula sobre
a chave**: ela varre o store, lê a identidade que o próprio objeto carrega e,
depois de remover, **confere que sumiu** — e reprova se sobrou.

**Why:** medido em 2026-09-16 na zona `wj_dyn` viva: 24.933 arquivos para 13.738
chaves, **11.189 chaves com mais de um objeto**. O nginx guarda um arquivo por
valor de `Vary: Accept-Encoding`, e o nome da variante é
`md5(md5_bruto(chave) + b"accept-encoding:" + valor + b"\r\n")` — **não é
derivável da chave sozinha**, depende do que o cliente mandou. `purge-origin-cache`
apagava `md5(chave)` e saía 0; o teste dele cobrava que a fórmula reproduzisse a
`proxy_cache_key` do `.conf` (e exigia, com nome, um host `127.0.0.1:8088` que
**nenhuma** das 13.738 chaves tinha). Cinco dias de `wikijuridica-edge-frescor`
em `failed` com `pos_purga_velhas` repetindo `origem_cache_velha_total`
(794≈796, 297=297, 48=48, 8=8, 6=6): a purga da origem nunca funcionou, e o
número que dizia "invalidei" era `len(rotas)`, não ausência medida.

**How to apply:** vale para qualquer store endereçado por hash com chave
secundária (Vary, sharding, dedupe por conteúdo). Três perguntas antes de
aceitar um invalidador: (1) o seletor **lê** o store ou **adivinha** o nome?
(2) o número que ele reporta é efeito medido ou intenção? (3) o teste compara
CONJUNTO ("quantos sobraram para esta rota") ou fórmula? Fórmula vira teste de
autoconsistência — se ela acha no disco algo que a varredura não indexou, o
parser quebrou —, nunca a forma de selecionar. E a ordem importa: purgar a borda
com a origem velha **repopula o velho** (medido em `/noticias/index.md`: `MISS`
em 1,11 s com o corpo antigo; com a origem invalidada antes, `MISS` em 1,03 s
com o corpo novo). Relacionado: [[censo-de-detector-orfao]],
[[mutante-de-fiacao-precisa-compilar]].
