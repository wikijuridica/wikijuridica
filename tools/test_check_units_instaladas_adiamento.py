#!/usr/bin/env python3
"""Bancada do ADIAMENTO DECLARADO de timer em `check-units-instaladas`.

POR QUE ESTA BANCADA EXISTE, com o caso que a originou
------------------------------------------------------
Em 2026-09-16 o passo 0a de `tools/deploy-publico` recusou a republicacao do
acervo inteiro porque dois `.timer` estavam inativos. Os dois estavam inativos
DE PROPOSITO, e por causa concreta:

  - `wikijuridica-bing-ai-citation.timer` so pode rodar depois de o titular
    autenticar a conta Microsoft no perfil do :99. Antes disso toda execucao
    sai 2 e o `OnFailure` acorda o dono TODO DIA pela mesma divida conhecida.
  - `wikijuridica-cerebro-saude.timer` alarmaria a cada 15 minutos enquanto
    `data/ops/cerebro_batimento.json` nao existisse.

A regra `timer_inativo` esta certa — serie parada e serie que ninguem ve parar.
O que faltava era distinguir "ninguem habilitou por esquecimento" de "nao pode
ser habilitado ainda, e esta escrito por que". Sem essa distincao o unico
remedio oferecido (`enable --now`) TROCAVA um gate vermelho por um alarme falso
diario — e alarme que toca todo dia pela mesma causa deixa de ser lido.

O QUE ESTA BANCADA PROTEGE, e e por isso que ela existe em vez de uma allowlist
------------------------------------------------------------------------------
Allowlist sem prazo vira deposito; guarda que filtra em silencio cria ponto cego
invisivel. As quatro invariantes abaixo sao o que impede isso, e cada uma tem
mutante que a mata:

  1. adiamento VALIDO vira AVISO (visivel), nao silencio;
  2. adiamento VENCIDO volta a REPROVAR;
  3. adiamento de timer JA ATIVO reprova como `adiamento_obsoleto`;
  4. registro ILEGIVEL sai 2 ("NAO MEDIDO"), nunca "nada adiado".
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools/check-units-instaladas"
REGISTRO_REAL = RAIZ / "ops/systemd/timers-adiados.jsonl"

TIMER = """[Unit]
Description=Timer de teste

[Timer]
OnCalendar=daily

[Install]
WantedBy=timers.target
"""


def registro(unit="wikijuridica-teste.timer", vence="2999-01-01", adiado="2026-09-16", **extra):
    reg = {
        "unit": unit,
        "motivo": "motivo de teste, com fato verificavel.",
        "destrava": "ato concreto que remove a dependencia.",
        "adiado_em": adiado,
        "vence_em": vence,
    }
    reg.update(extra)
    return reg


class Cenario:
    """Diretorio de units + registro de adiamento, isolados do repositorio."""

    def __init__(self, linhas, unidades=("wikijuridica-teste.timer",)):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.dir_units = base / "units"
        self.dir_units.mkdir()
        for nome in unidades:
            (self.dir_units / nome).write_text(TIMER, encoding="utf-8")
        self.dir_etc = base / "etc"
        self.dir_etc.mkdir()
        for nome in unidades:
            os.symlink(self.dir_units / nome, self.dir_etc / nome)
        self.registro = base / "adiados.jsonl"
        corpo = []
        for linha in linhas:
            corpo.append(linha if isinstance(linha, str) else json.dumps(linha, ensure_ascii=False))
        self.registro.write_text("\n".join(corpo) + ("\n" if corpo else ""), encoding="utf-8")

    def roda(self, hoje="2026-09-16", extra=()):
        # --sem-systemctl mantem o teste puro de arquivo: as regras de runtime
        # saem como NAO MEDIDAS e nao dependem do systemd da maquina.
        cmd = [sys.executable, str(GATE), "--dir", str(self.dir_units), "--etc", str(self.dir_etc),
               "--adiamentos", str(self.registro), "--hoje", hoje, "--json",
               "--sem-systemctl", *extra]
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.tmp.cleanup()


def problemas(proc):
    return json.loads(proc.stdout)["problemas"]


def regras(proc):
    return sorted(p["regra"] for p in problemas(proc))


class TesteRegistroIlegivelNaoViraNadaAdiado(unittest.TestCase):
    """Invariante 4. Um arquivo corrompido nao pode valer como autorizacao."""

    def test_json_invalido_sai_2(self):
        with Cenario(["{isto nao e json"]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIn("ilegivel", p.stderr)

    def test_campo_faltando_sai_2(self):
        reg = registro()
        del reg["destrava"]
        with Cenario([reg]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIn("destrava", p.stderr)

    def test_campo_vazio_sai_2(self):
        """String vazia e a forma silenciosa de nao declarar motivo."""
        with Cenario([registro(motivo="")]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIn("motivo", p.stderr)

    def test_data_fora_do_formato_sai_2(self):
        with Cenario([registro(vence="16/10/2026")]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertIn("vence_em", p.stderr)

    def test_vencimento_anterior_ao_inicio_sai_2(self):
        with Cenario([registro(adiado="2026-09-16", vence="2026-09-01")]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_unit_adiada_duas_vezes_sai_2(self):
        """Qual linha vale nao e derivavel do arquivo: nao se escolhe por ordem."""
        with Cenario([registro(vence="2026-09-20"), registro(vence="2999-01-01")]) as c:
            p = c.roda()
            self.assertEqual(p.returncode, 2, p.stdout + p.stderr)

    def test_arquivo_ausente_e_estado_legitimo(self):
        """Nada adiado e o caso comum, e nao pode virar INCONCLUSIVO."""
        with Cenario([]) as c:
            os.remove(c.registro)
            p = c.roda()
            self.assertNotEqual(p.returncode, 2, p.stdout + p.stderr)


class TesteComentarioEBranco(unittest.TestCase):
    def test_comentario_e_linha_branca_nao_quebram(self):
        with Cenario(["# cabecalho explicativo", "", json.dumps(registro(), ensure_ascii=False)]) as c:
            p = c.roda()
            self.assertNotEqual(p.returncode, 2, p.stdout + p.stderr)
            self.assertNotIn("adiamento_orfao", regras(p))


class TesteOrfao(unittest.TestCase):
    """Linha morta num registro de excecao e o comeco do deposito."""

    def test_adiamento_para_unit_inexistente_reprova(self):
        with Cenario([registro(unit="wikijuridica-nao-existe.timer")]) as c:
            p = c.roda()
            self.assertIn("adiamento_orfao", regras(p))
            self.assertEqual(p.returncode, 1)


class TesteMutacao(unittest.TestCase):
    """Os mutantes que este arquivo existe para matar.

    Cada um desliga UMA das quatro invariantes. Se algum passar verde, a regra
    correspondente nao esta sendo cobrada e o registro vira allowlist.
    """

    def test_mutante_sem_conferir_vencimento(self):
        """Mutante: `reg["vence_em"] < hoje` -> `False`.

        Com ele, um adiamento de 2026-09-01 continuaria valendo para sempre, que
        e exatamente a allowlist que este desenho recusa ser. A data do teste e
        POSTERIOR ao vencimento, e o gate tem de reprovar nomeando o registro.
        """
        with Cenario([registro(vence="2026-09-20")]) as c:
            p = c.roda(hoje="2026-09-21")
            self.assertEqual(p.returncode, 1, "adiamento vencido deixou de reprovar")
            self.assertIn("adiamento_vencido", regras(p))
            detalhe = " ".join(x["detalhe"] for x in problemas(p))
            self.assertIn("VENCEU", detalhe, "a mensagem nao diz que o prazo venceu")
            self.assertIn("2026-09-20", detalhe, "a mensagem nao traz a data do vencimento")
            self.assertIn("Destrava", detalhe, "a mensagem vencida nao diz o que remove a dependencia")

    def test_vencido_nao_e_silenciado_por_aviso(self):
        """O vencido sai de `problemas`, nunca so de `avisos`.

        Sem esta assercao, trocar o `reprova` por `avisos.append` deixaria o
        gate verde com o prazo estourado — e o aviso viraria o disfarce.
        """
        with Cenario([registro(vence="2026-09-20")]) as c:
            p = c.roda(hoje="2026-09-21")
            avisos = json.loads(p.stdout)["avisos"]
            self.assertFalse([a for a in avisos if "ADIADO" in a],
                             "adiamento vencido continuou anunciado como valido")

    def test_no_dia_do_vencimento_ainda_vale(self):
        """Fronteira explicita: `>=`, nao `>`. Escrita antes do numero."""
        with Cenario([registro(vence="2026-09-20")]) as c:
            p = c.roda(hoje="2026-09-20")
            self.assertNotIn("timer_inativo", regras(p))

    def test_mutante_que_silencia_em_vez_de_avisar(self):
        """Mutante: trocar o `avisos.append` por `pass`.

        Adiamento que nao aparece na saida e ponto cego invisivel — o defeito
        que `guarda-esconde-o-que-filtra` registra. O aviso e obrigatorio.
        """
        with Cenario([registro()]) as c:
            p = c.roda()
            avisos = json.loads(p.stdout)["avisos"]
            casados = [a for a in avisos if "wikijuridica-teste.timer" in a]
            self.assertTrue(casados, "adiamento valido sumiu da saida")
            texto = casados[0]
            self.assertIn("ADIADO", texto)
            self.assertIn("2999-01-01", texto, "o aviso nao diz ate quando vale")
            self.assertIn("Destrava", texto, "o aviso nao diz o que remove a dependencia")

    def test_adiamento_valido_nao_reprova_nada(self):
        """Controle negativo. Adiamento em dia nao pode inventar problema.

        Foi este caso que pegou um defeito REAL do gate em 2026-09-16: a
        primeira versao casava o registro com a unit so dentro do ramo de
        runtime, entao com `--sem-systemctl` um adiamento perfeitamente valido
        era acusado de `adiamento_orfao`. A regra de arquivo nasceu dai.
        """
        with Cenario([registro()]) as c:
            p = c.roda()
            self.assertEqual(problemas(p), [], "adiamento valido gerou problema")
            self.assertEqual(p.returncode, 0)


class TesteRegistroRealDoRepositorio(unittest.TestCase):
    """O arquivo que esta em producao tem de ser legivel e estar em dia.

    Controle positivo: se o registro real ficar vazio, este teste passa por
    vacuidade — por isso ele tambem cobra que, havendo linha, ela seja completa.
    """

    def test_registro_real_e_legivel_e_completo(self):
        if not REGISTRO_REAL.exists():
            self.skipTest("nenhum timer adiado hoje")
        vistos = 0
        for n, linha in enumerate(REGISTRO_REAL.read_text(encoding="utf-8").splitlines(), 1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            reg = json.loads(linha)
            vistos += 1
            for campo in ("unit", "motivo", "destrava", "adiado_em", "vence_em"):
                self.assertTrue(reg.get(campo), f"linha {n}: campo {campo} ausente ou vazio")
            self.assertTrue((RAIZ / "ops/systemd" / reg["unit"]).exists(),
                            f"linha {n}: {reg['unit']} nao existe em ops/systemd/")
            self.assertGreater(len(reg["motivo"]), 40,
                               f"linha {n}: motivo curto demais para explicar o que acontece hoje")
        self.assertGreater(vistos, 0, "registro so com comentario: remova o arquivo em vez de deixa-lo vazio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
