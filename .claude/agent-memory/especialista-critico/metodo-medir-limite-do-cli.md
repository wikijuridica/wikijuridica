---
name: metodo-medir-limite-do-cli
description: Como medir constante/comportamento do Claude Code lendo o bundle ELF instalado (grep -a -b -o + dd), em vez de acreditar na documentação
metadata:
  type: reference
---

O CLI instalado é um ELF Bun com o bundle JS embutido em
`~/.local/share/claude/versions/<versao>` (~209 MB). Ele é a autoridade sobre
qualquer limite do harness — a documentação arredonda ("25 KB" pode ser 25.000
ou 25.600) e o número que vale é o literal que executa.

Receita medida em 2026-09-16 (custo: segundos, `nice -n 19`):

1. Confirme QUAL binário executa: `readlink -f /proc/<pid>/exe` dos processos
   `claude` — pode não ser a versão mais nova instalada.
2. Ache a âncora por string literal:
   `grep -a -b -o -F "auto-memory, persists across conversations" <bin>` devolve
   o offset em byte.
3. Leia a janela: `dd if=<bin> bs=1 skip=$((off-4000)) count=7000 | tr -d '\000'`.
4. Siga os nomes minificados (`function ynt`, `var iL=200,F1=25000`) com o mesmo
   `grep -a -b -o -F`, sempre **dentro da mesma faixa de offset**: nomes de 2-3
   letras se repetem entre chunks e casar o homônimo de outro chunk é o erro
   fácil.
5. Para um teste que não apodreça, case por **padrão de forma**, não por nome:
   `grep -a -c -E '=200,[A-Za-z0-9_$]{1,4}=25000,'` deu exatamente 1 ocorrência
   em 2.1.266, 2.1.267 e 2.1.268 — o nome muda a cada build, a tupla não.

Cuidado registrado: `byteCount` do harness é `n.length` do JS, ou seja **unidade
UTF-16**, não byte UTF-8 — em PT-BR acentuado a diferença é ~3,4% e inverte o
veredito de um gate. Ver [[criterio-migracao-memoria-para-rules]].
