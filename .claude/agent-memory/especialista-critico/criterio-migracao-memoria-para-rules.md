---
name: criterio-migracao-memoria-para-rules
description: Critério para tirar um ponteiro do MEMORY.md e deixar a lição numa .claude/rules — cobertura INTEIRA mais equivalência de GATILHO, que é a parte que ninguém escreve
metadata:
  type: feedback
---

Migrar memória para `.claude/rules/*.md` com `paths:` só é ganho quando as duas
condições valem — a segunda é a que costuma faltar:

1. **Cobertura inteira**: a rule contém o caso, o número e o "how to apply". Se
   cobre metade, a correção é completar a rule, nunca remover deixando a lição
   pela metade.
2. **Equivalência de gatilho**: a lição só precisa existir **no momento em que
   uma ferramenta toca um arquivo do `paths:`**. Rule carrega por toque de
   arquivo (o Read empurra o caminho em `nestedMemoryAttachmentTriggers`), não
   quando o agente *pensa* em fazer algo. Lição de postura, de decisão ou que
   vale antes de escolher a rota (ex.: "parser antes de modelo", "não estreitar
   com número curto") **não tem gatilho de arquivo** e fica no índice.

Três consequências práticas, todas medidas em 2026-09-16 no `/opt/wiki`:

- **Alargue o `paths:` até o arquivo do caso medido.** A regra do JSON de
  produtor Go não casava `data/editorial/refined_public_prose.jsonl`, que é o
  arquivo do próprio incidente das 7.959 linhas. Regra que não carrega no
  arquivo do incidente não protege ninguém.
- **A rule que absorve nomeia o arquivo de origem** (`Memórias de origem:
  \`x.md\``). É o que separa "absorvida" de "órfã" para
  `tools/check-memoria-no-limite`, e é prova por máquina de que a lição migrou em
  vez de sumir. O `.md` da memória **nunca** se apaga: some só a linha do índice.
- **Valide o glob com a semântica certa** (gitignore/`ignore`, com `x/**`
  virando `x`): `pathspec.PathSpec.from_lines('gitwildmatch', …)` com casos
  positivos E controle negativo. Glob morto é rule morta e não aparece em teste
  nenhum.

**Why:** o índice é o que carrega sempre e é ele que tem teto; a rule é grátis no
índice mas só existe no toque. Trocar um pelo outro sem olhar o gatilho move a
lição para um lugar onde ela nunca chega.

**How to apply:** antes de remover a linha, escreva a frase "esta lição é
necessária quando alguém TOCA <arquivo>". Se a frase ficar falsa, não migre.
Ver [[metodo-medir-limite-do-cli]].
