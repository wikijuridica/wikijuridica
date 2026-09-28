#!/usr/bin/env python3
"""Prova por MUTAÇÃO que `check-normative-freshness` reprova pelo motivo certo, e
que ele NÃO reprova pelos motivos errados.

O gate nasceu de um achado: `tools/generate-normative-fingerprint-baseline-20260812`
tem o modo `reconferencia` desde 2026-08-12 e **nunca rodou** — a bancada roda o
selftest, que prova as propriedades do instrumento e não emite veredito nenhum
sobre o acervo. Ao rodar a reconferência pela primeira vez, em 2026-09-10:
113 documentos com impressão diferente, e o CPC (`l13105`) — citado em 3.502
páginas publicadas — com `ano_max` 2025 → 2026 pela Lei 15.484/2026.

O §5 do contrato manda: "Detector novo nasce com teste de falso positivo sobre
amostra real (já houve detector que acusou 46 páginas e as 46 eram falso
positivo)". As três classes que o gate NÃO pode acusar estão aqui como casos
próprios, e cada uma tem uma razão medida:

  - `marcacao`: o Planalto reeditou o HTML e o texto normativo é o mesmo. Foram
    8 dos 16 classificados na primeira medição.
  - `indeterminado`: um dos lados não tinha impressão — quase sempre acórdão do
    STJ servido por `GetInteiroTeorDoAcordao`, que monta HTML por requisição.
    Foram 15 dos 31 documentos.
  - alteração com alcance ZERO no acervo: norma que mudou e que nenhuma página
    cita não é dívida editorial.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools/check-normative-freshness"


def linha_de_serie(documentos, date="2026-09-10", comparado="base-anterior.jsonl"):
    return {
        "schema": "normative_freshness_v1",
        "date": date,
        "comparado_com": comparado,
        "ferramenta": "tools/generate-normative-freshness",
        "alteracao_legislativa": sum(1 for d in documentos
                                     if d["classe"] == "alteracao_legislativa"),
        "marcacao": sum(1 for d in documentos if d["classe"] == "marcacao"),
        "documentos": documentos,
        "counts_as_audience": False,
    }


def documento(nome, classe="alteracao_legislativa", paginas=10,
              normas=("Lei 15484/2026",), ano=(2025, 2026)):
    return {
        "documento": nome,
        "classe": classe,
        "paginas_que_citam": paginas,
        "normas_novas": list(normas),
        "ano_max_anterior": ano[0],
        "ano_max_atual": ano[1],
    }


class Frescor(unittest.TestCase):
    def roda(self, documentos, ciencia=(), extra=()):
        """Executa o gate contra uma raiz temporária e devolve (exit, saída)."""
        with tempfile.TemporaryDirectory() as diretorio:
            raiz = Path(diretorio)
            (raiz / "data/ops").mkdir(parents=True)
            (raiz / "tools").mkdir(parents=True)
            # O gate resolve os caminhos a partir do PRÓPRIO arquivo, então a
            # cópia tem de morar na árvore temporária — apontar --root não
            # existe aqui de propósito: o gate lê dois arquivos fixos e ler
            # caminho de fora seria superfície que ninguém usa.
            copia = raiz / "tools/check-normative-freshness"
            copia.write_text(GATE.read_text(encoding="utf-8"), encoding="utf-8")
            copia.chmod(0o755)
            serie = raiz / "data/ops/normative_freshness_daily.jsonl"
            serie.write_text(json.dumps(linha_de_serie(documentos),
                                        ensure_ascii=False) + "\n", encoding="utf-8")
            if ciencia:
                (raiz / "data/ops/normative_freshness_ciencia.jsonl").write_text(
                    "\n".join(json.dumps(c, ensure_ascii=False) for c in ciencia) + "\n",
                    encoding="utf-8")
            concluido = subprocess.run(
                [sys.executable, str(copia), "--json", "--dias-de-tolerancia", "99999",
                 *extra],
                capture_output=True, text=True, timeout=60)
            return concluido.returncode, concluido.stdout + concluido.stderr

    # --- o que ELE TEM de acusar ------------------------------------------
    def test_alteracao_legislativa_com_alcance_reprova(self):
        codigo, saida = self.roda([documento("planalto/l13105.htm", paginas=3502)])
        self.assertEqual(codigo, 1, saida)
        self.assertIn('"pendentes_sem_ciencia": 1', saida)
        self.assertIn('"paginas_alcancadas": 3502', saida)

    def test_o_alcance_e_somado_entre_documentos(self):
        codigo, saida = self.roda([
            documento("planalto/l13105.htm", paginas=3502),
            documento("planalto/l5172.htm", paginas=139,
                      normas=("Lei Complementar 236/2026",)),
        ])
        self.assertEqual(codigo, 1, saida)
        self.assertIn('"paginas_alcancadas": 3641', saida)

    # --- o que ele NÃO pode acusar (falso positivo) ------------------------
    def test_marcacao_nao_reprova(self):
        codigo, saida = self.roda([documento("planalto/l14133.htm", classe="marcacao",
                                             paginas=16, normas=())])
        self.assertEqual(codigo, 0, saida)
        self.assertIn('"passou": true', saida)

    def test_indeterminado_nao_reprova(self):
        codigo, saida = self.roda([documento("stj/acordao", classe="indeterminado",
                                             paginas=5, normas=())])
        self.assertEqual(codigo, 0, saida)

    def test_alteracao_sem_alcance_no_acervo_nao_reprova(self):
        codigo, saida = self.roda([documento("planalto/l15321.htm", paginas=0)])
        self.assertEqual(codigo, 0, saida)

    # --- o ledger de ciência ----------------------------------------------
    def test_ciencia_registrada_libera_o_documento(self):
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502)],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10", "veredito": "revisado",
                      "por": "Rafael Toledo", "nota": "conferido"}])
        self.assertEqual(codigo, 0, saida)

    def test_ciencia_de_OUTRA_norma_nao_libera(self):
        """Tomar ciência de uma alteração não dá quitação para a próxima: se a
        mesma norma voltar a mudar, com outra alteradora, o gate reprova de novo.
        Sem isto, uma linha de ciência escrita hoje calaria o documento para
        sempre — que é o oposto do que o ledger existe para fazer."""
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502,
                       normas=("Lei 15900/2027",))],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10", "veredito": "revisado"}])
        self.assertEqual(codigo, 1, saida)

    def test_ciencia_de_UMA_das_alteradoras_nao_libera(self):
        """A lista `normas_novas` vem ORDENADA, e escolher um elemento dela por
        posicao foi o defeito da primeira versao deste gate: o CTN aparecia sob
        "Lei Complementar 118/2005" enquanto a alteracao que importava era a
        LC 236/2026. Todas precisam de ciencia."""
        codigo, saida = self.roda(
            [documento("planalto/l5172.htm", paginas=139,
                       normas=("Lei Complementar 118/2005",
                               "Lei Complementar 236/2026"))],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "revisado"}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("Lei Complementar 118/2005", saida)

    def test_asterisco_cobre_todas_as_alteradoras_da_rodada(self):
        codigo, saida = self.roda(
            [documento("planalto/l5172.htm", paginas=139,
                       normas=("Lei Complementar 118/2005",
                               "Lei Complementar 236/2026"))],
            ciencia=[{"documento": "planalto/l5172.htm", "norma_alteradora": "*",
                      "ciencia_em": "2026-09-10", "veredito": "revisado"}])
        self.assertEqual(codigo, 0, saida)

    def test_em_revisao_nao_libera(self):
        """Trabalho comecado nao e trabalho feito. Se `em_revisao` liberasse, o
        gate ficaria mudo no minuto em que o achado aparece — quitacao sem
        leitura, que e o oposto do que o ledger existe para fazer."""
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502)],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao"}])
        self.assertEqual(codigo, 1, saida)

    def test_sem_efeito_no_acervo_libera(self):
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502)],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10",
                      "veredito": "sem_efeito_no_acervo"}])
        self.assertEqual(codigo, 0, saida)

    def test_veredito_desconhecido_nao_libera(self):
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502)],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10", "veredito": "tudo_certo"}])
        self.assertEqual(codigo, 1, saida)

    def test_ledger_sem_veredito_e_invalido(self):
        """Linha de ciência sem veredito é ciência que não diz nada. O gate
        recusa o ledger inteiro em vez de aceitá-la como quitação."""
        codigo, saida = self.roda(
            [documento("planalto/l13105.htm", paginas=3502)],
            ciencia=[{"documento": "planalto/l13105.htm",
                      "norma_alteradora": "Lei 15484/2026",
                      "ciencia_em": "2026-09-10"}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("ledger de ciencia invalido", saida)

    # --- memória do ledger: a série esquece, ele não ----------------------
    def test_em_revisao_do_ledger_reprova_mesmo_fora_da_serie(self):
        """A SÉRIE DE AMANHÃ NÃO TRAZ O ACHADO DE HOJE, e é por isso que este
        teste existe.

        `generate-normative-freshness` compara a coleta contra o baseline
        VIGENTE. Assim que o baseline é regravado, o documento alterado entra
        nele como estado atual e some da série. Se o gate lesse só a série, a
        pendência `em_revisao` escrita hoje — 111 páginas do CTN por revisar —
        viraria verde amanhã sozinha, sem ninguém ler nada. Quitação por
        esquecimento é pior que gate ausente: ela parece trabalho feito."""
        codigo, saida = self.roda(
            [documento("planalto/l14133.htm", classe="marcacao", paginas=16,
                       normas=())],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn("l5172", saida)
        self.assertIn('"pendentes_do_ledger_em_revisao": 1', saida)
        self.assertIn('"paginas_alcancadas": 111', saida)

    def test_conclusao_posterior_encerra_a_pendencia_do_ledger(self):
        """O trabalho se declara concluído ESCREVENDO, não deixando de escrever:
        uma linha posterior com `revisado` para o mesmo par (documento, norma)
        encerra a pendência aberta antes. Sem isto, `em_revisao` seria uma
        armadilha permanente e a única saída seria apagar a linha — que é
        exatamente o que o ledger existe para impedir."""
        codigo, saida = self.roda(
            [documento("planalto/l14133.htm", classe="marcacao", paginas=16,
                       normas=())],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111},
                     {"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-12", "veredito": "revisado",
                      "nota": "as 4 paginas que enumeram o art. 151 foram corrigidas"}])
        self.assertEqual(codigo, 0, saida)
        self.assertIn('"pendentes_do_ledger_em_revisao": 0', saida)

    def test_conclusao_de_OUTRA_norma_nao_encerra_a_pendencia(self):
        """Encerrar é por par (documento, norma alteradora). Concluir a revisão
        da LC 118/2005 não quita a LC 236/2026 no mesmo documento."""
        codigo, saida = self.roda(
            [documento("planalto/l14133.htm", classe="marcacao", paginas=16,
                       normas=())],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111},
                     {"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 118/2005",
                      "ciencia_em": "2026-09-12", "veredito": "revisado"}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn('"pendentes_do_ledger_em_revisao": 1', saida)

    def test_documento_na_serie_E_no_ledger_conta_uma_vez_so(self):
        """O documento que aparece nos dois lados não pode somar o alcance duas
        vezes: `paginas_alcancadas` é população, não contagem de ocorrências."""
        codigo, saida = self.roda(
            [documento("planalto/l5172.htm", paginas=139,
                       normas=("Lei Complementar 236/2026",))],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn('"pendentes_sem_ciencia": 1', saida)
        self.assertIn('"paginas_alcancadas": 139', saida)

    def test_conclusao_com_asterisco_encerra_pendencia_aberta_por_nome(self):
        """`"*"` numa conclusão vale por todas as alteradoras do documento. O
        ledger vivo abriu as pendências do CTN com `"*"` justamente porque a
        LC 236/2026 mudou o diploma inteiro; a conclusão tem de poder fechá-las
        sem que quem escreve precise repetir a lista de então."""
        codigo, saida = self.roda(
            [documento("planalto/l14133.htm", classe="marcacao", paginas=16,
                       normas=())],
            ciencia=[{"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111},
                     {"documento": "planalto/l5172.htm", "norma_alteradora": "*",
                      "ciencia_em": "2026-09-12", "veredito": "revisado"}])
        self.assertEqual(codigo, 0, saida)
        self.assertIn('"pendentes_do_ledger_em_revisao": 0', saida)

    def test_conclusao_por_nome_nao_encerra_pendencia_aberta_com_asterisco(self):
        """O inverso NÃO vale. Pendência aberta com `"*"` declarou o documento
        inteiro em revisão; concluir uma alteradora só cobre menos do que se
        declarou, e liberar aí seria quitação parcial passando por completa."""
        codigo, saida = self.roda(
            [documento("planalto/l14133.htm", classe="marcacao", paginas=16,
                       normas=())],
            ciencia=[{"documento": "planalto/l5172.htm", "norma_alteradora": "*",
                      "ciencia_em": "2026-09-10", "veredito": "em_revisao",
                      "paginas_que_citam": 111},
                     {"documento": "planalto/l5172.htm",
                      "norma_alteradora": "Lei Complementar 236/2026",
                      "ciencia_em": "2026-09-12", "veredito": "revisado"}])
        self.assertEqual(codigo, 1, saida)
        self.assertIn('"pendentes_do_ledger_em_revisao": 1', saida)

    # --- frescor da própria série -----------------------------------------
    def test_serie_velha_reprova_mesmo_sem_pendencia(self):
        """Gate que lê medição parada é gate desligado."""
        with tempfile.TemporaryDirectory() as diretorio:
            raiz = Path(diretorio)
            (raiz / "data/ops").mkdir(parents=True)
            (raiz / "tools").mkdir(parents=True)
            copia = raiz / "tools/check-normative-freshness"
            copia.write_text(GATE.read_text(encoding="utf-8"), encoding="utf-8")
            copia.chmod(0o755)
            (raiz / "data/ops/normative_freshness_daily.jsonl").write_text(
                json.dumps(linha_de_serie([documento("x", classe="marcacao", normas=())],
                                          date="2026-01-01"), ensure_ascii=False) + "\n",
                encoding="utf-8")
            concluido = subprocess.run(
                [sys.executable, str(copia), "--json", "--dias-de-tolerancia", "8"],
                capture_output=True, text=True, timeout=60)
        self.assertEqual(concluido.returncode, 1, concluido.stdout)
        self.assertIn('"passou": false', concluido.stdout)

    def test_serie_ausente_devolve_2_e_nao_1(self):
        """Ausência de medição é inconclusivo, não reprovação: exit 2 diz 'não
        consegui medir', exit 1 diz 'medi e está errado'. Confundir os dois faz
        o alerta do dono tratar infra como defeito de conteúdo."""
        with tempfile.TemporaryDirectory() as diretorio:
            raiz = Path(diretorio)
            (raiz / "tools").mkdir(parents=True)
            copia = raiz / "tools/check-normative-freshness"
            copia.write_text(GATE.read_text(encoding="utf-8"), encoding="utf-8")
            copia.chmod(0o755)
            concluido = subprocess.run([sys.executable, str(copia)],
                                       capture_output=True, text=True, timeout=60)
        self.assertEqual(concluido.returncode, 2, concluido.stderr)


if __name__ == "__main__":
    unittest.main()
