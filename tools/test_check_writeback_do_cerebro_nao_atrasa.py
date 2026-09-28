#!/usr/bin/env python3
"""Bancada de tools/check-writeback-do-cerebro-nao-atrasa.

O gate mede se o produtor que leva a extracao do cerebro para o corpus
(`cmd/generate-writeback-extracoes`) parou de rodar. O que ele NAO pode fazer e
confundir tres coisas que o arquivo append-only mostra iguais: trabalho pendente,
trabalho impossivel (precedente sem URN) e trabalho DESFEITO por uma revisao mais
estrita do proprio cerebro.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GATE = RAIZ / "tools" / "check-writeback-do-cerebro-nao-atrasa"


def agora_menos(horas: float) -> str:
    quando = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=horas)
    return quando.strftime("%Y-%m-%dT%H:%M:%SZ")


def extracao(id_fonte: str, urns: list[str], horas: float, **extra) -> dict:
    registro = {
        "schema_version": "extracao_dispositivos_v1",
        "chave": "acordao:STJ:" + id_fonte,
        "id_fonte": id_fonte,
        "modelo": "qwen3.5:4b",
        "dispositivos": [{"norma": "n", "artigo": "", "urn": u} for u in urns],
        "gerado_em": agora_menos(horas),
    }
    registro.update(extra)
    return registro


def monta(base: Path, extracoes: list[dict], promovidos: list[str]) -> None:
    (base / "data" / "ai").mkdir(parents=True, exist_ok=True)
    with (base / "data" / "ai" / "extracoes_dispositivos.jsonl").open("w", encoding="utf-8") as saida:
        for registro in extracoes:
            saida.write(json.dumps(registro, ensure_ascii=False) + "\n")
    with (base / "data" / "ai" / "dispositivos_promovidos.jsonl").open("w", encoding="utf-8") as saida:
        for id_fonte in promovidos:
            saida.write(json.dumps({"id_fonte": id_fonte,
                                    "promovido_em": agora_menos(0)}) + "\n")


def roda(base: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), "--raiz", str(base), *extra],
                          capture_output=True, text=True)


class Bancada(unittest.TestCase):
    def test_pendente_antigo_reprova_e_ensina_o_produtor(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao("000812714", ["sumula:STJ:7"], horas=50)], [])
            r = roda(base)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("000812714", r.stdout)
            self.assertIn("generate-writeback-extracoes", r.stdout)

    def test_revisao_mais_estrita_que_esvazia_NAO_e_pendencia(self):
        """URN retirada por revisão mais estrita é trabalho DESFEITO, não pendente.

        Foi o defeito real da primeira versão deste gate: ele somava todas as
        linhas do arquivo append-only e acusou 21 pendentes, das quais 12 eram
        acórdãos que a revisão `norma_atestada_v1` reprocessou e esvaziou de
        propósito. Cobrar a promoção deles seria mandar reintroduzir o que o
        cérebro acabou de recusar.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [
                extracao("000812714", ["sumula:STJ:7"], horas=50),
                extracao("000812714", [], horas=10, revisao="norma_atestada_v1",
                         descartados_norma_nao_atestada=1),
            ], [])
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("pendentes com URN: 0", r.stdout)

    def test_reextracao_que_MANTEM_a_urn_continua_pendente(self):
        """Controle negativo do caso acima: última linha ainda com URN reprova."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [
                extracao("000812714", ["sumula:STJ:7"], horas=60),
                extracao("000812714", ["sumula:STJ:7"], horas=50),
            ], [])
            r = roda(base)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("pendentes com URN: 1", r.stdout)

    def test_um_pendente_antigo_no_meio_de_recentes_ainda_reprova(self):
        """A idade que decide é a do MAIS ANTIGO, não a do último a chegar.

        Sem este caso, trocar `min` por `max` na escolha do pendente sobrevive:
        com fila cheia de itens recentes, o mais novo tem sempre 0 h e o gate
        ficaria verde para sempre — exatamente o modo de falha que ele existe
        para pegar, porque writeback parado acumula fila NOVA em cima da velha.
        """
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao("000812714", ["sumula:STJ:7"], horas=50)]
                  + [extracao(str(700000 + i), ["sumula:STJ:7"], horas=1)
                     for i in range(5)], [])
            r = roda(base)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("000812714", r.stdout)

    def test_precedente_sem_urn_nao_e_pendencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao("000812714", [""], horas=99)], [])
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fila_recente_e_regime_normal(self):
        """O cérebro trabalha 24/7 e a onda promove 1x/dia: fila não é defeito."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao(str(700000 + i), ["sumula:STJ:7"], horas=3)
                         for i in range(40)], [])
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("fila normal", r.stdout)
            self.assertIn("pendentes com URN: 40", r.stdout)

    def test_ja_promovido_sai_da_conta(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao("000812714", ["sumula:STJ:7"], horas=99)],
                  ["000812714"])
            r = roda(base)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("pendentes com URN: 0", r.stdout)

    def test_cardinalidade_vem_antes_de_qualquer_chave(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao(str(700000 + i), ["sumula:STJ:7"], horas=99)
                         for i in range(30)], [])
            r = roda(base)
            linhas = r.stdout.splitlines()
            self.assertTrue(linhas[0].startswith("linhas de extracao: 30"), linhas[0])
            self.assertIn("acordaos distintos: 30", linhas[0])
            primeira_chave = next(i for i, l in enumerate(linhas) if "700000" in l)
            self.assertGreater(primeira_chave, 0)
            self.assertIn("e mais 10", r.stdout)

    def test_arquivo_ausente_nao_e_defeito(self):
        """Raiz de bancada sem cérebro nenhum: nada a promover é resposta certa."""
        with tempfile.TemporaryDirectory() as tmp:
            r = roda(Path(tmp))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_linha_torta_aborta_dizendo_arquivo_e_linha(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            monta(base, [extracao("000812714", ["sumula:STJ:7"], horas=1)], [])
            alvo = base / "data" / "ai" / "extracoes_dispositivos.jsonl"
            alvo.write_text(alvo.read_text(encoding="utf-8") + "{nao e json\n",
                            encoding="utf-8")
            r = roda(base)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("linha 2", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
