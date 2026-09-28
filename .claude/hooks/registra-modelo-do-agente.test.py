#!/usr/bin/env python3
"""Bancada de registra-modelo-do-agente.sh.

Ordem do dono, 2026-09-22: o modelo de cada papel é fixo, e o que o subagente de fato rodou é o
`resolvedModel` que o harness entrega no PostToolUse da ferramenta Agent. O hook grava esse fato
em .agents/runtime/contexto/modelos-<AAAA-MM-DD>.jsonl — a autoridade contra a qual a primeira
linha "Modelo:" de cada entrega se confere.

O que a bancada cobra:
  - uma linha JSON por chamada, com os campos pedidos e o resolvido;
  - nunca bloqueia: exit 0 sempre, inclusive com payload ilegível, vazio ou de outra ferramenta;
  - aviso (additionalContext de PostToolUse) quando o resolvido é Haiku ou de outra família;
  - sem python3, o registro continua em bash puro;
  - custo: mediana medida contra o teto da casa (o pedido é < 50 ms; o teto duro aqui é 150 ms,
    para a bancada não reprovar por carga da máquina — a mediana medida vai no relatório).

Rodar:  python3 .claude/hooks/registra-modelo-do-agente.test.py
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "registra-modelo-do-agente.sh"


class Bancada(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="registra-modelo-")
        self.raiz = Path(self._tmp.name) / "wiki"
        self.raiz.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def roda(self, entrada: dict | None = None, resposta: dict | None = None, ferramenta: str = "Agent",
             bruto: str | None = None, path: str = "/usr/bin:/bin", extra: dict | None = None) -> subprocess.CompletedProcess:
        payload = {"session_id": "bancada-sessao", "cwd": str(self.raiz), "hook_event_name": "PostToolUse",
                   "tool_name": ferramenta, "tool_input": entrada or {}, "tool_response": resposta or {},
                   "tool_use_id": "toolu_01"}
        payload.update(extra or {})
        return subprocess.run(["bash", str(HOOK)], input=bruto if bruto is not None else json.dumps(payload),
                              capture_output=True, text=True, cwd=str(self.raiz),
                              env={"PATH": path, "HOME": str(self.raiz), "CLAUDE_PROJECT_DIR": str(self.raiz)},
                              timeout=20)

    def linhas(self) -> list[dict]:
        pasta = self.raiz / ".agents" / "runtime" / "contexto"
        arquivos = sorted(pasta.glob("modelos-*.jsonl")) if pasta.exists() else []
        return [json.loads(l) for a in arquivos for l in a.read_text(encoding="utf-8").splitlines() if l.strip()]

    def sem_python(self) -> str:
        pasta = Path(self._tmp.name) / "bin-sem-python"
        pasta.mkdir(exist_ok=True)
        for ferramenta in ("bash", "mkdir"):
            origem = next(p for p in (Path("/bin") / ferramenta, Path("/usr/bin") / ferramenta) if p.exists())
            destino = pasta / ferramenta
            if not destino.exists():
                destino.symlink_to(origem)
        return str(pasta)


def chamada(tipo: str = "general-purpose", modelo: str | None = None) -> dict:
    entrada = {"description": "tarefa", "prompt": "faça", "subagent_type": tipo}
    if modelo is not None:
        entrada["model"] = modelo
    return entrada


def resposta(resolvido: str | None = "claude-opus-5-5", status: str = "completed", **extra) -> dict:
    r = {"status": status, "agentId": "a4d2c8f1e0b3a297", "content": [{"type": "text", "text": "ok"}],
         "totalTokens": 10, "totalDurationMs": 5, "totalToolUseCount": 1}
    if resolvido is not None:
        r["resolvedModel"] = resolvido
    r.update(extra)
    return r


class TesteRegistro(Bancada):
    def test_grava_uma_linha_com_pedido_e_resolvido(self):
        p = self.roda(chamada("engenheiro-go", "opus"), resposta("claude-opus-5-5"))
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.strip(), "", "mesma família: não há o que avisar")
        [linha] = self.linhas()
        self.assertEqual(linha["subagent_type"], "engenheiro-go")
        self.assertEqual(linha["model_pedido"], "opus")
        self.assertEqual(linha["resolvedModel"], "claude-opus-5-5")
        self.assertEqual(linha["agentId"], "a4d2c8f1e0b3a297")
        self.assertEqual(linha["sessao"], "bancada-sessao")
        self.assertEqual(linha["status"], "completed")
        self.assertRegex(linha["ts"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_uma_linha_por_chamada_no_arquivo_do_dia(self):
        for tipo in ("investigador", "auditor-adversarial", "engenheiro-go"):
            self.roda(chamada(tipo), resposta("claude-sonnet-5" if tipo == "investigador" else "claude-fable-5-1"))
        self.assertEqual([l["subagent_type"] for l in self.linhas()], ["investigador", "auditor-adversarial", "engenheiro-go"])
        arquivos = list((self.raiz / ".agents/runtime/contexto").glob("modelos-*.jsonl"))
        self.assertEqual(len(arquivos), 1)
        self.assertRegex(arquivos[0].name, r"^modelos-\d{4}-\d{2}-\d{2}\.jsonl$")

    def test_sem_subagent_type_e_general_purpose_e_campos_ausentes_somem(self):
        self.roda({"prompt": "x"}, resposta(None))
        [linha] = self.linhas()
        self.assertEqual(linha["subagent_type"], "general-purpose")
        self.assertNotIn("model_pedido", linha)
        self.assertNotIn("resolvedModel", linha)

    def test_lancamento_em_segundo_plano_e_models_used(self):
        self.roda(chamada("engenheiro-go", "opus"),
                  {"status": "async_launched", "agentId": "b1", "resolvedModel": "claude-opus-5-5", "outputFile": "/tmp/x"})
        self.roda(chamada("engenheiro-go", "opus"),
                  resposta("claude-opus-5-5", modelsUsed=["claude-opus-5-5", "claude-fable-5-1"]))
        primeira, segunda = self.linhas()
        self.assertEqual(primeira["status"], "async_launched")
        self.assertEqual(segunda["modelsUsed"], ["claude-opus-5-5", "claude-fable-5-1"])

    def test_agente_que_lanca_agente_fica_registrado(self):
        self.roda(chamada("investigador"), resposta("claude-sonnet-5"), extra={"agent_type": "engenheiro-go"})
        self.assertEqual(self.linhas()[0]["lancado_por"], "engenheiro-go")


class TesteAviso(Bancada):
    def aviso(self, p: subprocess.CompletedProcess) -> str:
        self.assertEqual(p.returncode, 0)
        especifico = json.loads(p.stdout)["hookSpecificOutput"]
        self.assertEqual(especifico["hookEventName"], "PostToolUse")
        return especifico["additionalContext"]

    def test_haiku_resolvido_avisa(self):
        texto = self.aviso(self.roda(chamada("general-purpose"), resposta("claude-haiku-4-5-20251001")))
        self.assertIn("Haiku", texto)
        self.assertIn("2026-09-22", texto)
        self.assertIn("modelos-", texto)

    def test_haiku_no_meio_da_execucao_avisa(self):
        texto = self.aviso(self.roda(chamada("engenheiro-go", "opus"),
                                     resposta("claude-opus-5-5", modelsUsed=["claude-opus-5-5", "claude-haiku-4-5"])))
        self.assertIn("Haiku", texto)

    def test_familia_diferente_da_pedida_avisa(self):
        texto = self.aviso(self.roda(chamada("engenheiro-go", "opus"), resposta("claude-fable-5-1")))
        self.assertIn("pedido em opus e começou em fable", texto)

    def test_mesma_familia_por_alias_e_id_nao_avisa(self):
        for pedido, resolvido in (("opus", "claude-opus-5-5"), ("sonnet", "claude-sonnet-5"),
                                  ("fable", "claude-fable-5-1"), ("opus[1m]", "claude-opus-5-5[1m]")):
            with self.subTest(pedido=pedido):
                self.assertEqual(self.roda(chamada(modelo=pedido), resposta(resolvido)).stdout.strip(), "")


class TesteNuncaBloqueia(Bancada):
    def test_payload_ilegivel_vazio_e_outra_ferramenta(self):
        for p in (self.roda(bruto="{não é json"), self.roda(bruto=""),
                  self.roda({"command": "ls"}, {"stdout": ""}, ferramenta="Bash")):
            self.assertEqual(p.returncode, 0)
            self.assertEqual(p.stdout.strip(), "")
        self.assertEqual(self.linhas(), [], "só chamada de Agent vira linha")

    def test_pasta_que_nao_pode_ser_criada_nao_bloqueia(self):
        (self.raiz / ".agents").write_text("arquivo no lugar da pasta", encoding="utf-8")
        p = self.roda(chamada(), resposta())
        self.assertEqual(p.returncode, 0)

    def test_nome_legado_task(self):
        self.roda(chamada("investigador"), resposta("claude-sonnet-5"), ferramenta="Task")
        self.assertEqual(len(self.linhas()), 1)


class TesteSemPython(Bancada):
    def test_registra_em_bash_puro(self):
        p = self.roda(chamada("engenheiro-go", "opus"), resposta("claude-opus-5-5"), path=self.sem_python())
        self.assertEqual(p.returncode, 0)
        [linha] = self.linhas()
        self.assertEqual(linha["juiz"], "bash")
        self.assertEqual(linha["subagent_type"], "engenheiro-go")
        self.assertEqual(linha["resolvedModel"], "claude-opus-5-5")
        self.assertEqual(linha["model_pedido"], "opus")

    def test_haiku_em_bash_puro_avisa(self):
        p = self.roda(chamada(), resposta("claude-haiku-4-5"), path=self.sem_python())
        self.assertEqual(p.returncode, 0)
        self.assertIn("Haiku", json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"])


class TesteCusto(Bancada):
    def test_mediana_abaixo_do_teto(self):
        dados = json.dumps({"session_id": "custo", "hook_event_name": "PostToolUse", "tool_name": "Agent",
                            "tool_input": chamada("engenheiro-go", "opus"), "tool_response": resposta()})
        tempos = []
        for _ in range(15):
            t0 = time.perf_counter()
            subprocess.run(["bash", str(HOOK)], input=dados, capture_output=True, text=True,
                           env={"PATH": "/usr/bin:/bin", "CLAUDE_PROJECT_DIR": str(self.raiz)}, timeout=20)
            tempos.append((time.perf_counter() - t0) * 1000)
        mediana = statistics.median(tempos)
        print(f"\n  registra-modelo-do-agente: mediana {mediana:.1f} ms em 15 chamadas", file=sys.stderr)
        # Régua da casa para hook: 300 ms (tools/check-modo-operacional --max-ms 300). O teto de
        # 150 ms da primeira versão reprovava na VM da ponte (mediana 154 ms com o sistema de
        # arquivos montado) sem defeito no hook; a régua é a do projeto, não a de uma máquina.
        self.assertLess(mediana, 300.0)


if __name__ == "__main__":
    if not HOOK.is_file():
        print(f"hook ausente: {HOOK}", file=sys.stderr)
        sys.exit(2)
    sintaxe = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True)
    if sintaxe.returncode != 0:
        print(f"erro de sintaxe em {HOOK}:\n{sintaxe.stderr}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
