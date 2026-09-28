#!/usr/bin/env python3
"""Testes de tools/generate-retorno-por-rota sobre 5 eventos sinteticos em 2 dias.
Contagem independente: dia 1 tem /mcp 10 (2 paths) + /x/index.md 3 + html 7 = 20;
dia 2 tem /api/v1/lote 4 e uma linha sem `requisicoes` (GA4) que e ignorada."""
import importlib.machinery, importlib.util, json, pathlib, subprocess, sys, tempfile, unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
GERADOR = RAIZ / "tools" / "generate-retorno-por-rota"


def carrega():
    loader = importlib.machinery.SourceFileLoader("gen_retorno", str(GERADOR))
    spec = importlib.util.spec_from_loader("gen_retorno", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


EVENTOS = [
    {"date": "2026-09-07", "path": "/mcp", "requisicoes": 6, "agentes_de_ia": 0, "por_agente": {"sentineloracle": 4, "humano_ou_nao_identificado": 2}},
    {"date": "2026-09-07", "path": "/mcp/", "requisicoes": 4, "agentes_de_ia": 0, "por_agente": {"mcpbeat": 4}},
    {"date": "2026-09-07", "path": "/familia/x/index.md", "requisicoes": 3, "agentes_de_ia": 3, "por_agente": {"gptbot": 3}},
    {"date": "2026-09-07", "path": "/familia/x/", "requisicoes": 7, "agentes_de_ia": 1, "por_agente": {"humano_ou_nao_identificado": 6, "perplexitybot": 1}},
    {"date": "2026-09-08", "path": "/api/v1/lote", "requisicoes": 4, "agentes_de_ia": 0, "por_agente": {"humano_ou_nao_identificado": 4}, "por_cliente_oauth": {"wj_abc": 3}},
    {"date": "2026-09-08", "fonte": "ga4", "sessoes": 12},
]


class TestRetornoPorRota(unittest.TestCase):
    def test_familias_e_contagens(self):
        mod = carrega()
        saida = mod.agrega(EVENTOS)
        self.assertEqual(len(saida), 2 * len(mod.FAMILIAS))
        por = {(r["date"], r["familia"]): r for r in saida}
        self.assertEqual(por[("2026-09-07", "/mcp")]["requisicoes"], 10)
        self.assertEqual(por[("2026-09-07", "/mcp")]["paths_distintos"], 2)
        self.assertEqual(por[("2026-09-07", "/mcp")]["por_agente"], {"sentineloracle": 4, "mcpbeat": 4, "humano_ou_nao_identificado": 2})
        self.assertEqual(por[("2026-09-07", "gemea.md")]["agentes_de_ia"], 3)
        self.assertEqual(por[("2026-09-07", "html")]["requisicoes"], 7)
        self.assertEqual(por[("2026-09-07", "/mcp")]["pct_do_dia"], 50.0)
        self.assertEqual(por[("2026-09-08", "/api/v1/lote")]["requisicoes"], 4)
        self.assertEqual(por[("2026-09-08", "/api/v1/lote")]["por_cliente_oauth"], {"wj_abc": 3})
        self.assertEqual(por[("2026-09-08", "/api/v1/lote")]["clientes_identificados"], 1)
        self.assertEqual(por[("2026-09-07", "/mcp")]["clientes_identificados"], 0)
        self.assertEqual(por[("2026-09-08", "/changes.json")]["requisicoes"], 0)  # zero explicito, sem buraco
        self.assertEqual(por[("2026-09-08", "html")]["requisicoes"], 0)

    def test_familia_fechada(self):
        mod = carrega()
        self.assertEqual(mod.familia("/.well-known/mcp/server-card.json"), "descritores")
        self.assertEqual(mod.familia("/openapi.json"), "descritores")
        self.assertEqual(mod.familia("/llms-full.txt"), "/llms*.txt")
        self.assertEqual(mod.familia("/api/v1/health"), "/api/v1/outros")
        self.assertEqual(mod.familia("/a2a/"), "/a2a")
        self.assertEqual(mod.familia("/trabalhista/y/"), "html")

    def test_cli_reescreve_o_arquivo_inteiro(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = pathlib.Path(d)
            (raiz / "data" / "ops" / "eventos").mkdir(parents=True)
            (raiz / "data" / "ops" / "eventos" / "eventos-2026-09-07.jsonl").write_text("\n".join(json.dumps(e) for e in EVENTOS) + "\n")
            for _ in range(2):
                proc = subprocess.run([sys.executable, str(GERADOR), "--root", str(raiz)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
            linhas = (raiz / "data" / "ops" / "retorno_por_rota_daily.jsonl").read_text().splitlines()
            self.assertEqual(len(linhas), 2 * 11)  # idempotente: duas execucoes, um arquivo
            self.assertEqual(json.loads(linhas[0])["schema_version"], "retorno_por_rota_daily_v1")


if __name__ == "__main__":
    unittest.main()
