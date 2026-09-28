#!/usr/bin/env python3
"""O classificador regressão × dívida tem de continuar ligado ao pre-commit.

POR QUE ESTA BANCADA NASCEU (2026-09-10), e o erro que ela impede.

`tools/check-baseline-testes-vermelhos` separa as duas coisas que a palavra
"vermelho" junta: falha FORA do baseline é REGRESSÃO (reprova o commit), e teste
do baseline que voltou a passar é baseline INFLADO (também reprova, porque dívida
paga tem de sair da lista). Todo veredito de commit depende dessa distinção.

Procurei o consumidor dele em `tools/`, `ops/` e `.claude/hooks/`, não achei
nenhum, e quase publiquei que ele era "o 312º órfão". **Ele está ligado desde
sempre — em `.githooks/pre-commit:735`**, e eu não o vi porque este repositório
usa `core.hooksPath=.githooks`, não `.claude/hooks`. Ausência num diretório que eu
escolhi não é ausência: é a memória `ausencia-de-sinal-nao-e-evidencia`, e o custo
teria sido uma seção inteira de dossiê afirmando o contrário do que o código faz.

E ele está ligado no lugar CERTO, o que é o detalhe que fecha o argumento: o
pre-commit o alimenta com `$LOG_TESTE_FOCADO`, a execução dos pacotes TOCADOS,
isolada — exatamente a condição em que `data/ops/testes_vermelhos_conhecidos.json`
foi medido (o registro de `internal/v2ingest` diz `duracao_s: 561.331`, que é o
pacote sozinho). Comparar com o log da `suite-completa`, que roda tudo em
paralelo, seria comparar populações diferentes: medido nos logs de 2026-09-05 e
2026-09-07, a suíte acusa 83 e 80 falhas nesse pacote contra as 3 do baseline.

Rodar:
    python3 tools/test_baseline_vermelhos_esta_ligado.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRE_COMMIT = RAIZ / ".githooks" / "pre-commit"
CLASSIFICADOR = RAIZ / "tools" / "check-baseline-testes-vermelhos"
BASELINE = RAIZ / "data" / "ops" / "testes_vermelhos_conhecidos.json"


class LigacaoNoPreCommit(unittest.TestCase):
    def setUp(self):
        self.texto = PRE_COMMIT.read_text(encoding="utf-8")

    def test_o_pre_commit_chama_o_classificador(self):
        self.assertIn("tools/check-baseline-testes-vermelhos", self.texto,
                      "o classificador ficou orfao: nenhum commit separa mais "
                      "regressao de divida")

    def test_ele_recebe_o_log_do_teste_FOCADO_e_nao_o_da_suite(self):
        """A condição da medição é parte do veredito.

        O baseline foi medido com o pacote SOZINHO. O log da suíte completa vem
        de uma execução em paralelo com todos os outros pacotes, e nele o mesmo
        `internal/v2ingest` acusa 80 falhas contra as 3 do baseline. Trocar a
        fonte por `suite-completa.log` transformaria o gate numa máquina de ~77
        falsos positivos por dia — e gate cuja saída inteira é falso positivo
        deixa de ser lido, que é o dano que ele existe para evitar.
        """
        self.assertIn('"$LOG_TESTE_FOCADO"', self.texto)
        self.assertNotIn("suite-completa.log", self.texto)

    def test_o_hooks_path_do_repo_aponta_para_githooks(self):
        """Se o hooksPath mudar, a ligação acima deixa de valer em silêncio."""
        saida = subprocess.run(["git", "-C", str(RAIZ), "config", "core.hooksPath"],
                               capture_output=True, text=True)
        self.assertEqual(saida.stdout.strip(), ".githooks",
                         "core.hooksPath mudou: confira onde o pre-commit vive agora")

    def test_o_shell_do_pre_commit_continua_valido(self):
        resultado = subprocess.run(["bash", "-n", str(PRE_COMMIT)],
                                   capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)


class ClassificadorSobreLogSintetico(unittest.TestCase):
    """O gate em si, no par que importa: regressão reprova, dívida tolera."""

    def roda(self, linhas: list[str]) -> subprocess.CompletedProcess:
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False,
                                         encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas) + "\n")
            caminho = arquivo.name
        return subprocess.run([sys.executable, str(CLASSIFICADOR), caminho],
                              capture_output=True, text=True)

    def baseline_do_pacote(self) -> tuple[str, str]:
        dados = json.loads(BASELINE.read_text(encoding="utf-8"))
        for pacote, registro in (dados.get("por_pacote") or {}).items():
            testes = registro.get("testes") or []
            if testes:
                return pacote, testes[0]
        self.skipTest("baseline sem pacote com teste nomeado")

    def test_falha_fora_do_baseline_e_regressao(self):
        pacote, _ = self.baseline_do_pacote()
        resultado = self.roda([
            "--- FAIL: TestQueNinguemBaselinou (0.01s)",
            f"FAIL\t{pacote}\t1.234s",
        ])
        saida = resultado.stdout + resultado.stderr
        self.assertEqual(resultado.returncode, 1, saida)
        self.assertIn("TestQueNinguemBaselinou", saida,
                      "a regressao tem de ser NOMEADA, nao so contada")

    def test_falha_que_esta_no_baseline_e_tolerada(self):
        pacote, teste = self.baseline_do_pacote()
        resultado = self.roda([
            f"--- FAIL: {teste} (0.01s)",
            f"FAIL\t{pacote}\t1.234s",
        ])
        self.assertEqual(resultado.returncode, 0,
                         "divida ja nomeada nao pode reprovar commit alheio: "
                         + resultado.stdout + resultado.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
