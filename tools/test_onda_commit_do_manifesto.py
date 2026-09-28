#!/usr/bin/env python3
"""Bancada do diagnostico acumulado da etapa 8.05/9 de tools/run-daily-content.

POR QUE ELA EXISTE (P1b, 2026-09-16). A etapa 8.05/9 commita
`published_manifest.jsonl` e `first_published_at.json` depois da publicacao, e
ela e LOAD-BEARING: e desse commit que a etapa 7.95/9 deriva a data de estreia
no ciclo seguinte. Ela NAO interrompe a onda -- parar depois de publicar
deixaria `.br` velho ao lado de HTML novo e o servidor sem recarga --, entao a
unica coisa que separa "falha tratada" de "falha silenciosa" e o alarme.

E alarme que ninguem executa e o defeito N3 deste mesmo arquivo: um
`registra_aviso` cujo comentario prometia anotar no ledger e que so fazia
`printf` para um stderr redirecionado para /dev/null. No-op total, por meses.

O ramo do alarme so roda quando o commit FALHA, o que nao acontece numa passada
normal. Por isso a bancada EXTRAI o bloco do arquivo real, entre as duas ancoras
literais, e o executa com uma data forjada. Reimplementar a aritmetica aqui
provaria a aritmetica do teste, nao a do arquivo que roda as 04:20.
"""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ONDA = RAIZ / "tools" / "run-daily-content"
INICIO = "# INICIO DO DIAGNOSTICO ACUMULADO 8.05/9"
FIM = "# FIM DO DIAGNOSTICO ACUMULADO 8.05/9"


def bloco_do_diagnostico() -> str:
    """As linhas verbatim do arquivo real, entre as ancoras."""
    fonte = ONDA.read_text(encoding="utf-8")
    inicio = fonte.find(INICIO)
    fim = fonte.find(FIM)
    if inicio < 0 or fim < 0 or fim <= inicio:
        raise AssertionError(
            f"ancoras do diagnostico 8.05/9 nao encontradas em {ONDA} — "
            "se o bloco mudou de lugar, a bancada tem de acompanhar; "
            "sem as ancoras ela mediria nada e passaria sempre"
        )
    return fonte[inicio:fim]


def executa(hoje: str, ultimo: str) -> tuple[int, str, str]:
    """Roda o bloco com `registra` dublado, que e o que se quer observar."""
    bloco = bloco_do_diagnostico()
    roteiro = "\n".join([
        "set -uo pipefail",
        'registra() { echo "REGISTRA:$1"; }',
        f'HOJE="{hoje}"',
        f'ULTIMO_COMMIT_DO_MANIFESTO="{ultimo}"',
        bloco,
    ])
    saida = subprocess.run(["bash", "-c", roteiro], capture_output=True, text=True)
    return saida.returncode, saida.stdout, saida.stderr


class TesteDiagnosticoAcumulado(unittest.TestCase):
    def test_seis_dias_sem_commit_emitem_chave_propria(self):
        """A janela real: o manifesto ficou de 2026-09-10 a 2026-09-16 sem commit,
        e 999 rotas ficaram sem evidencia datada nenhuma."""
        codigo, stdout, stderr = executa("2026-09-16", "2026-09-10")
        self.assertEqual(codigo, 0, f"o bloco nao pode falhar: {stderr}")
        self.assertIn("REGISTRA:commit:manifesto-acumulado-6d", stdout)
        self.assertIn("6 dias sem commit do manifesto", stderr)

    def test_dois_dias_ja_e_acumulado(self):
        """O limiar e 2 porque uma falha isolada custa UM dia de precisao no
        registro (a etapa 7.95/9 reconcilia pelo teto da revisao); duas seguidas
        significam causa nao transitoria."""
        codigo, stdout, _ = executa("2026-09-16", "2026-09-14")
        self.assertEqual(codigo, 0)
        self.assertIn("REGISTRA:commit:manifesto-acumulado-2d", stdout)

    def test_um_dia_nao_escala(self):
        """Controle negativo: sem ele, um bloco que gritasse SEMPRE passaria nos
        dois testes acima e o alarme perderia significado."""
        codigo, stdout, stderr = executa("2026-09-16", "2026-09-15")
        self.assertEqual(codigo, 0)
        self.assertNotIn("acumulado", stdout)
        self.assertNotIn("ACUMULADO", stderr)

    def test_mesmo_dia_nao_escala(self):
        codigo, stdout, _ = executa("2026-09-16", "2026-09-16")
        self.assertEqual(codigo, 0)
        self.assertNotIn("acumulado", stdout)

    def test_sem_commit_anterior_nao_quebra(self):
        """Repositorio em que o manifesto nunca foi commitado: `git log` devolve
        vazio, e o bloco tem de sair quieto em vez de fazer aritmetica com ''."""
        codigo, stdout, stderr = executa("2026-09-16", "")
        self.assertEqual(codigo, 0, f"data vazia nao pode derrubar o bloco: {stderr}")
        self.assertNotIn("acumulado", stdout)

    def test_a_chave_carrega_o_numero_de_dias(self):
        """Chave sem o numero viraria uma linha igual todo dia no relatorio, e
        `registra` e justamente o que o dono le de manha."""
        _, stdout, _ = executa("2026-09-30", "2026-09-10")
        self.assertIn("REGISTRA:commit:manifesto-acumulado-20d", stdout)

    def test_o_bloco_extraido_e_o_do_arquivo_real(self):
        """Se alguem trocar o limiar ou a chave no arquivo, esta bancada tem de
        enxergar -- ela le o arquivo, nao uma copia."""
        bloco = bloco_do_diagnostico()
        self.assertIn("DIAS_SEM_COMMIT", bloco)
        self.assertIn("commit:manifesto-acumulado-", bloco)
        self.assertRegex(bloco, re.compile(r"DIAS_SEM_COMMIT >= 2"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
