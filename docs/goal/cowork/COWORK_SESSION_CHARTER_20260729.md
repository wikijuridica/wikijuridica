# Cowork Fable 5 — Charter da sessão 2026-07-29 (tarde)

Agente: `cowork-fable-20260729` (Cowork desktop, sandbox `focused-kind-bohr`).
Ordem do dono (verbatim, resumida): fechar o gap de ~2k páginas v2 com no mínimo
10 agentes por frente (advogados-pesquisadores de fonte, redatores jurídicos,
adversariais/especialistas); auditar e corrigir comandos com falso-positivo/
falso-negativo e peso desnecessário; nunca excluir página — reprovada =
reaproveitar/reescrever; commits para frente, sem pendência; não confiar cegamente
em comando/conteúdo/arquitetura do repo; performance é requisito (fábrica para
milhões, foco nos 10k).

## Capacidades medidas deste ambiente (2026-07-29, sandbox Cowork)

| Capacidade | Estado | Evidência |
| --- | --- | --- |
| Rede para fontes oficiais | OK | `curl` planalto/lexml → 200 |
| `os.replace` (rename) no mount | OK | probe em `tools/_tmp_probe_rename_*` |
| DELETE no mount (bash) | **BLOQUEADO** | `unlink` → EPERM (proteção Cowork) |
| `/opt/wiki` no bash do sandbox | **INEXISTENTE** | path real: `/sessions/focused-kind-bohr/mnt/wiki`; symlink/unshare negados |
| File tools (Read/Write/Edit) | veem `/opt/wiki` | via host, fora do sandbox |
| python3 | 3.10.12 | sem `renameat2(NOREPLACE)` garantido (presence falhou nisso) |
| node | v22.22.3 | |
| git commit | testado neste commit | este arquivo é o teste |

Consequências operacionais para agentes desta sessão:
1. Comando bash usa SEMPRE o path `/sessions/focused-kind-bohr/mnt/wiki`; as
   funções CAS do produtor recebem o root como argumento (nunca dependem de
   `/opt/wiki` implícito). File tools usam `/opt/wiki`.
2. Ferramenta que só roda com `/opt/wiki` hardcoded (ex.: `check-writing-mass-dispatch`,
   `ROOT` fixo) ganha override por env/flag como melhoria para frente — nunca fork drift.
3. Nada de deletar: sobra de probe/tmp fica classificada no `.gitignore` (já coberto).
4. `tools/generate-coord-presence` falha neste ambiente por `renameat2` — presença
   desta sessão registrada por este charter e pelo bus (`generate-coord-message`).

## Plano de ondas (mínimo 10 agentes por frente)

- **Onda F — fontes (advogados-pesquisadores):** resolver chaves de
  `source_hint` sem entrada no catálogo (gargalo medido: 6.824 chaves distintas,
  17.514 referências; lane1 editorial = 1.711). Candidatos em
  `data/research/source_hint_curation/cowork-w2-agent-NN.jsonl`; aplicação SÓ
  pelo gerador CAS `tools/generate-curated-source-hints`.
- **Onda G — gates (especialistas + adversarial):** campanha sobre o dossiê
  `data/ops/command_audit_findings_20260729.jsonl` (72 defeitos; classes:
  armadilha-loop, falso-positivo, reprova-sem-orientar, escala, obsoleto).
  Correção na causa-raiz, para frente, nunca afrouxando gate.
- **Onda W — redatores jurídicos:** fila sancionada (`ops/relaunch-writing.sh` →
  lotes prontos) com o contrato integral do `writing-mass.js` (CAS + proveniência
  + auditor canônico). Reprovado = reescrever/reaproveitar; `v2_blocked_drafts/`
  para defeito de sistema; tombstone SÓ para fonte inexistente no mundo.
- **Fiscal:** agente vigia transcripts/saídas e red-teia amostras de texto.

Registro de continuidade: achados e integrações desta sessão vão em
`docs/goal/MAESTRO_CODEX_LOG.md` e commits leves por pathspec.
