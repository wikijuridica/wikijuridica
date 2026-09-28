---
name: metodo-payload-de-gerador-datado
description: Ao corrigir registro JÁ gravado (shard v2, portfólio), derive o payload fazendo o produtor corrigido serializar a linha e comparando byte a byte — nunca infira a string
metadata:
  type: feedback
---

Gerador datado que conserta registro já gravado **não escreve texto derivado de
raciocínio**: o payload tem de ser a saída do produtor corrigido, provada por um
teste que serializa a linha pelo MESMO serializador que gravou o shard e exige
igualdade **byte a byte** com o registro em disco.

**Why:** DEC-017 proíbe a máquina inventar prosa pública. Um payload inferido
("é só tirar o `j`") é palpite com CAS por cima: o CAS prova que ninguém mexeu
no registro, não que o texto novo é o certo. Em 2026-09-16, no reparo do title
de `/jurisprudencia/stj-resp-2218914/`, o oráculo mostrou que a igualdade valia
para a linha INTEIRA (10.004 B) e para o portfólio — e o mutante do produtor
serializou 10.011 B, os 7 bytes de uma ocorrência por sítio. Sem o oráculo eu
teria afirmado 7 sítios sem saber que eram 7, e sem saber que mais nada mudava.

**How to apply:** antes de escrever o gerador, ache a função do produtor que
monta o registro (`montaPagina`/`montaIntencao`) e o serializador
(`codificaJSONL`), rode-os sobre a fonte REAL num teste do pacote e compare com
a linha crua lida do shard — sem reserializar do lado do teste, que muda ordem
de chave e escape. Depois do reparo, converta a asserção em invariante
permanente (`produtor == gravado`), que passa a reprovar tanto recorrupção do
dado quanto regressão do produtor. Vale para qualquer
`tools/generate-*-repair-AAAAMMDD`. Ver [[fixture-que-e-o-alvo-do-trabalho]].
