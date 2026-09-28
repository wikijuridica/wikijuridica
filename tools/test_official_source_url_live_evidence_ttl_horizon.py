#!/usr/bin/env python3
"""Testes de tools/officialsourcettlhorizon.py — o censo de vencimento de TTL.

O teste central é ANTI-FALSO-NEGATIVO sobre AMOSTRA REAL, e o defeito que ele
persegue é específico: `checked_at` do arquivo derivado NÃO é sempre medição.
Quando não há tentativa válida, o agregado grava `checked_at = run_date`
(internal/officialsourceurlliveevidence/evidence.go:1370). Um detector que só
subtraia datas conta esses carimbos como "medição fresca" e responde "zero
vencidos" para sempre — foi assim que o revalidador de TTL antigo ficou cego.

Por isso os casos abaixo cobrem os DOIS lados:

  * o carimbo NÃO pode ser lido como medição (falso negativo do vencimento);
  * a medição de verdade NÃO pode ser lida como carimbo (falso positivo, que
    faria o job sondar fonte oficial à toa).

E o detector de divergência tem o seu próprio controle: o caso em que o derivado
legitimamente NÃO copia a medição vencida da fonte tem de continuar passando —
senão o gate acusaria o comportamento correto do agregado.

Rodar:
    python3 tools/test_official_source_url_live_evidence_ttl_horizon.py
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

import officialsourcettlhorizon as horizonte_ttl  # noqa: E402

MEDIDO = "official_source_live_metadata_attempted_blocked"
FALHOU = "official_source_live_metadata_failed_blocked"
PENDENTE = "official_source_live_metadata_attempt_pending_blocked"
PULADO = "official_source_live_metadata_skipped_registry_missing_blocked"
AUSENTE = "official_source_live_metadata_missing_blocked"


def registro(status, checked_at, ttl=60, **extra):
    base = {
        "live_evidence_status": status,
        "checked_at": checked_at,
        "freshness_ttl_days": ttl,
        "source_url_hash": extra.pop("source_url_hash", "hash-" + checked_at),
        "official_source_url": extra.pop("official_source_url", "https://www.planalto.gov.br/ccivil_03/x.htm"),
        "run_date": extra.pop("run_date", checked_at),
        "http_status_code": extra.pop("http_status_code", 200 if status == MEDIDO else 0),
        "content_type": extra.pop("content_type", "text/html" if status == MEDIDO else ""),
        "http_method": extra.pop("http_method", "HEAD"),
    }
    base.update(extra)
    return base


class TestClassificacaoDeCarimboVersusMedicao(unittest.TestCase):
    def test_carimbo_de_run_date_nunca_conta_como_medicao(self):
        for status in (PENDENTE, PULADO, AUSENTE):
            with self.subTest(status=status):
                linha = registro(status, "2026-09-05")
                self.assertFalse(horizonte_ttl.eh_medicao(linha),
                                 f"{status} tem checked_at = run_date, não medição")
                self.assertIsNone(horizonte_ttl.primeiro_dia_vencido(linha),
                                  f"{status} não tem relógio de TTL correndo")

    def test_medicao_de_verdade_conta_como_medicao(self):
        for status in (MEDIDO, FALHOU):
            with self.subTest(status=status):
                linha = registro(status, "2026-08-04")
                self.assertTrue(horizonte_ttl.eh_medicao(linha))
                self.assertIsNotNone(horizonte_ttl.primeiro_dia_vencido(linha))


class TestAritmeticaDoPrazo(unittest.TestCase):
    """O prazo tem de ser o MESMO que checkedAtFreshAt aplica em Go:
    fresco enquanto `run_date - checked_at <= ttl`, logo o primeiro dia vencido
    é `checked_at + ttl + 1`."""

    def test_primeiro_dia_vencido_e_checked_at_mais_ttl_mais_um(self):
        linha = registro(MEDIDO, "2026-08-04", ttl=60)
        self.assertEqual(horizonte_ttl.primeiro_dia_vencido(linha), datetime.date(2026, 10, 4))

    def test_ultimo_dia_fresco_ainda_nao_conta_como_vencido(self):
        censo = horizonte_ttl.horizonte([registro(MEDIDO, "2026-08-04", ttl=60)],
                                        datetime.date(2026, 10, 3))
        self.assertEqual(censo["vencidos_hoje"], 0, "checked_at + ttl ainda é fresco no Go")
        censo = horizonte_ttl.horizonte([registro(MEDIDO, "2026-08-04", ttl=60)],
                                        datetime.date(2026, 10, 4))
        self.assertEqual(censo["vencidos_hoje"], 1)

    def test_ttl_fora_da_faixa_cai_no_padrao_como_no_go(self):
        self.assertEqual(horizonte_ttl.ttl_do_registro({"freshness_ttl_days": 0}), 60)
        self.assertEqual(horizonte_ttl.ttl_do_registro({"freshness_ttl_days": 366}), 60)
        self.assertEqual(horizonte_ttl.ttl_do_registro({"freshness_ttl_days": 90}), 90)


class TestCensoSeparaAsDuasPopulacoes(unittest.TestCase):
    def test_carimbo_nao_entra_na_agenda_de_vencimento(self):
        censo = horizonte_ttl.horizonte(
            [registro(MEDIDO, "2026-08-04", ttl=60, source_url_hash="a"),
             registro(AUSENTE, "2026-09-05", ttl=60, source_url_hash="b"),
             registro(PULADO, "2026-09-05", ttl=90, source_url_hash="c")],
            datetime.date(2026, 9, 5))
        self.assertEqual(censo["medidos"], 1)
        self.assertEqual(censo["carimbos"], 2)
        self.assertEqual(censo["primeiro_vencimento"], "2026-10-04")
        self.assertEqual(censo["registros_no_primeiro_vencimento"], 1)
        self.assertEqual(censo["dias_ate_o_primeiro"], 29)
        self.assertEqual([linha["primeiro_dia_vencido"] for linha in censo["agenda"]], ["2026-10-04"])

    def test_status_desconhecido_e_denunciado_e_nao_engolido(self):
        censo = horizonte_ttl.horizonte([registro("official_source_live_metadata_status_novo", "2026-09-05")],
                                        datetime.date(2026, 9, 5))
        self.assertEqual(censo["desconhecidos"], 1,
                         "status novo tem de aparecer, nunca ser classificado em silêncio")
        self.assertEqual(censo["medidos"], 0)
        self.assertEqual(censo["carimbos"], 0)


class TestCensoDeSondagem(unittest.TestCase):
    """Quem entra na fila de sonda de uma passada `--live`.

    O erro perigoso aqui é contar o registro PULADO (sem match seguro no
    registro de fontes) como trabalho pendente: ele nunca será sondado enquanto
    o join não o alcançar, e contá-lo faz o job relatar fila eterna — o mesmo
    ruído que ensina o operador a ignorar o relatório.
    """

    def test_pulado_sem_match_nao_entra_na_fila(self):
        censo = horizonte_ttl.censo_de_sondagem(
            [registro(PULADO, "2026-09-05", source_url_hash="a")], datetime.date(2026, 9, 5))
        self.assertEqual(censo["sondaveis"], 0)
        self.assertEqual(censo["pulados_sem_match"], 1)

    def test_medicao_fresca_e_reaproveitada_sem_rede(self):
        censo = horizonte_ttl.censo_de_sondagem(
            [registro(MEDIDO, "2026-08-04", ttl=60, source_url_hash="a")], datetime.date(2026, 9, 5))
        self.assertEqual(censo["sondaveis"], 0)
        self.assertEqual(censo["frescos_reaproveitados"], 1)

    def test_medicao_vencida_volta_para_a_fila(self):
        censo = horizonte_ttl.censo_de_sondagem(
            [registro(MEDIDO, "2026-08-04", ttl=60, source_url_hash="a")], datetime.date(2026, 10, 4))
        self.assertEqual(censo["vencidos"], 1)
        self.assertEqual(censo["sondaveis"], 1)

    def test_medicao_negativa_volta_para_a_fila_mesmo_dentro_do_ttl(self):
        """reusablePositiveMetadataAttempt exclui 4xx/5xx de proposito: 404 de
        hoje nao prova que a fonte seguira fora do ar pelos 60 dias do TTL."""
        censo = horizonte_ttl.censo_de_sondagem(
            [registro(MEDIDO, "2026-09-05", http_status_code=404, source_url_hash="a")],
            datetime.date(2026, 9, 5))
        self.assertEqual(censo["negativos"], 1)
        self.assertEqual(censo["sondaveis"], 1)
        self.assertEqual(censo["frescos_reaproveitados"], 0)

    def test_amostra_real_fecha_a_conta(self):
        caminho = RAIZ / horizonte_ttl.CAMINHO_ATTEMPTS
        if not caminho.exists():
            raise AssertionError(f"amostra real ausente ({caminho})")
        censo = horizonte_ttl.censo_de_sondagem(horizonte_ttl.le_jsonl(str(caminho)), horizonte_ttl.hoje_utc())
        total = (censo["pendentes"] + censo["vencidos"] + censo["negativos"] +
                 censo["frescos_reaproveitados"] + censo["pulados_sem_match"] + censo["sem_classificacao"])
        registros = sum(1 for _ in horizonte_ttl.le_jsonl(str(caminho)))
        self.assertEqual(total, registros, "a soma das populações tem de fechar com o total de registros")
        self.assertEqual(censo["sem_classificacao"], 0,
                         "registro que nenhuma população reconhece: o censo ficaria mentindo por omissão")


class TestDivergenciaEntreFonteEDerivado(unittest.TestCase):
    def test_medicao_que_so_existe_no_derivado_e_denunciada(self):
        """A assinatura exata do produtor aposentado: sonda gravando no derivado."""
        fonte = horizonte_ttl.indexa_por_hash([registro(PENDENTE, "2026-09-05", source_url_hash="h1")])
        derivado = horizonte_ttl.indexa_por_hash([registro(MEDIDO, "2026-09-05", source_url_hash="h1")])
        conflito = horizonte_ttl.divergencias(fonte, derivado)
        self.assertEqual(conflito["divergentes"], 1)
        self.assertIn("medicao que a fonte nao tem", conflito["exemplos"][0]["motivo"])

    def test_checked_at_diferente_entre_as_camadas_e_denunciado(self):
        fonte = horizonte_ttl.indexa_por_hash([registro(MEDIDO, "2026-08-04", source_url_hash="h1")])
        derivado = horizonte_ttl.indexa_por_hash([registro(MEDIDO, "2026-09-05", source_url_hash="h1")])
        conflito = horizonte_ttl.divergencias(fonte, derivado)
        self.assertEqual(conflito["divergentes"], 1)
        self.assertIn("checked_at", conflito["exemplos"][0]["motivo"])

    def test_derivado_que_deixa_de_copiar_medicao_vencida_NAO_e_divergencia(self):
        """Controle de falso positivo.

        Quando a tentativa vence, GenerateAt deliberadamente não copia a medição
        e deixa o carimbo com `source_live_metadata_stale_invalid_or_future_for_run_date`.
        Acusar isso faria o gate reprovar o comportamento correto do agregado.
        """
        fonte = horizonte_ttl.indexa_por_hash([registro(MEDIDO, "2026-06-01", source_url_hash="h1")])
        derivado = horizonte_ttl.indexa_por_hash([registro(AUSENTE, "2026-09-05", source_url_hash="h1")])
        conflito = horizonte_ttl.divergencias(fonte, derivado)
        self.assertEqual(conflito["divergentes"], 0, conflito["exemplos"])


class TestAmostraReal(unittest.TestCase):
    """Amostra real, como o contrato exige de detector novo.

    Nada aqui depende da data de hoje: são invariantes do modelo de dado.
    """

    @classmethod
    def setUpClass(cls):
        cls.caminho_fonte = RAIZ / horizonte_ttl.CAMINHO_ATTEMPTS
        cls.caminho_derivado = RAIZ / horizonte_ttl.CAMINHO_DERIVADO
        # Ausência de amostra é FALHA, nunca skip: um teste que se pula sozinho
        # passa por não ter olhado nada, que é o falso verde deste repositório.
        for caminho in (cls.caminho_fonte, cls.caminho_derivado):
            if not caminho.exists():
                raise AssertionError(
                    f"amostra real ausente ({caminho}): sem ela este teste passaria por não ter olhado nada")

    def test_toda_medicao_real_tem_status_http_ou_erro_de_rede(self):
        medidos = carimbos = 0
        for linha in horizonte_ttl.le_jsonl(str(self.caminho_fonte)):
            if horizonte_ttl.eh_medicao(linha):
                medidos += 1
                codigo = int(linha.get("http_status_code") or 0)
                erro = str(linha.get("network_error_code") or "").strip()
                self.assertTrue(codigo > 0 or erro != "",
                                f"registro classificado como medição sem status HTTP nem erro de rede: "
                                f"{linha.get('official_source_url')}")
            else:
                carimbos += 1
                self.assertEqual(int(linha.get("http_status_code") or 0), 0,
                                 f"registro classificado como carimbo carrega status HTTP: "
                                 f"{linha.get('official_source_url')} -> {linha.get('http_status_code')}")
        self.assertGreater(medidos, 0, "amostra real sem nenhuma medição: o censo não teria o que medir")
        self.assertGreater(carimbos, 0, "amostra real sem nenhum carimbo: o caso perigoso sumiu do dado")

    def test_nenhum_status_da_amostra_real_escapa_da_classificacao(self):
        censo = horizonte_ttl.horizonte(horizonte_ttl.le_jsonl(str(self.caminho_fonte)),
                                        horizonte_ttl.hoje_utc())
        self.assertEqual(censo["desconhecidos"], 0,
                         f"status fora das duas famílias conhecidas: {json.dumps(censo['por_status'], ensure_ascii=False)}")
        self.assertEqual(censo["medidos"] + censo["carimbos"], censo["total"])

    def test_derivado_nao_carrega_medicao_que_a_fonte_de_verdade_nao_tem(self):
        """O guarda da família: qualquer produtor que volte a gravar no arquivo
        derivado aparece aqui, não importa em que linguagem ele seja escrito."""
        fonte = horizonte_ttl.indexa_por_hash(horizonte_ttl.le_jsonl(str(self.caminho_fonte)))
        derivado = horizonte_ttl.indexa_por_hash(horizonte_ttl.le_jsonl(str(self.caminho_derivado)))
        conflito = horizonte_ttl.divergencias(fonte, derivado)
        self.assertEqual(
            conflito["divergentes"], 0,
            "o arquivo derivado carrega medição ausente da fonte de verdade — algum produtor "
            "voltou a gravar em official_source_url_live_evidence.jsonl: "
            + json.dumps(conflito["exemplos"], ensure_ascii=False)[:2000])


if __name__ == "__main__":
    unittest.main(verbosity=2)
