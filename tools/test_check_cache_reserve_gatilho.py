#!/usr/bin/env python3
"""Testes de tools/check-cache-reserve-gatilho — gatilho diario + drift do Cache Reserve.

TODO teste roda OFFLINE: `LER_VIVO` e injetado; as series vem de arquivos
temporarios sob um WIKI_ROOT proprio. O parser e o fluxo sao os de producao.

O que fica travado, e por que:

  1. ABAIXO do limiar em 3 dias => "manter desligado", exit 0.
  2. ACIMA em 3 dias consecutivos => "LIGAR", exit 1, com o bot nomeado.
  3. 2 DIAS ACIMA + 1 ABAIXO => NAO liga. E a PROVA POR MUTACAO: o teste troca
     `all()` por `any()` no guarda `serie_consecutiva_acima` do proprio codigo
     fonte, executa o mutante e exige que ELE diga LIGAR. Se um dia o guarda
     virar codigo morto (ou alguem "simplificar" para qualquer dia acima), este
     teste fica vermelho. Os dois vereditos sao IMPRESSOS.
  4. DIA FALTANDO no meio quebra a sequencia: 90% + n/d + 90% nao liga.
  5. Regra 2 (misses_pre_head_sem_purga > 2% do acervo) liga sozinha.
  6. SEM SERIE (nem baseline, nem series brutas) => exit 2, e o gate nao
     inventa numero.
  7. FALLBACK das series brutas usa a ULTIMA linha por (date, agent_key), nunca
     a soma: a fixture e desenhada para que a soma cumulativa desse "manter"
     (5,0%, nao acima de 5) e a ultima linha desse "LIGAR" (8,0%). Foi a soma
     bruta que produziu os "0,3-0,9%" citados como premissa de D1.
  8. DRIFT: vivo `on` sem linha no ledger => exit 1 com "DRIFT"; vivo `on` COM
     linha da ferramenta => exit 1 com mensagem DISTINTA ("DESATUALIZADO");
     sem credencial => nao e drift, e o veredito do disco continua valendo.
  9. O canonico carrega os numeros do gatilho (5%, 3 dias, 2%, 10.141) -- o
     gate os le de la, entao mudar o gatilho e editar o JSON, com diff.

Rodar:
    python3 tools/test_check_cache_reserve_gatilho.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from unittest import mock

sys.dont_write_bytecode = True

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "check-cache-reserve-gatilho"
CANONICO = RAIZ / "ops" / "cloudflare" / "cache-reserve.json"

DIAS = ["2026-09-06", "2026-09-07", "2026-09-08"]
ARGS = ["--ate", "2026-09-08", "--dias", "3", "--json"]
BOTS = ("perplexitybot", "oai-searchbot", "bingbot")


def vivo(valor):
    def _ler(zona, caminho, env):
        return {"id": "cache_reserve", "value": valor,
                "modified_on": "2026-08-28T23:41:24.032957Z", "editable": True}, None
    return _ler


def vivo_indisponivel(zona, caminho, env):
    return None, "sem credencial Cloudflare (.env.local sem CLOUDFLARE_ZONE_TOKEN nem CLOUDFLARE_EMAIL+CLOUDFLARE_API_TOKEN)"


def linha_baseline(dia, travessias, misses=50):
    """Uma linha `cache_baseline_v1` com o formato que tools/generate-cache-baseline grava."""
    t = {}
    for bot, razao in travessias.items():
        if razao is None:
            t[bot] = {"origem": 0, "borda": 0, "travessia": None, "status": "nao_mensuravel"}
        else:
            t[bot] = {"origem": int(round(razao * 1000)), "borda": 1000, "travessia": razao, "status": "ok",
                      "borda_campo": "requests_sampled", "origem_campo": "requests_authentic"}
    return {"schema_version": "cache_baseline_v1", "date": dia, "graphql_disponivel": False,
            "travessia_por_bot": t,
            "misses_pre_head_sem_purga": {"total": misses, "varreduras_so_frios": 4,
                                          "varreduras_contadas": 3, "varreduras_excluidas_por_purga": 1,
                                          "purgas_durante_varredura": 0, "janela_s": 3600},
            "purgas_tudo": 0, "gerado_em": "2026-09-09T14:22:29+00:00"}


def grava_jsonl(caminho, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as fh:
        for l in linhas:
            fh.write(json.dumps(l, ensure_ascii=False) + "\n")


def raiz_temporaria(com_canonico=True):
    d = pathlib.Path(tempfile.mkdtemp(prefix="cache-reserve-gatilho-"))
    if com_canonico:
        destino = d / "ops" / "cloudflare"
        destino.mkdir(parents=True)
        shutil.copy(CANONICO, destino / "cache-reserve.json")
    (d / "data" / "ops").mkdir(parents=True)
    return d


def carrega(raiz, fonte=None):
    """Importa a ferramenta com WIKI_ROOT na arvore temporaria. Com `fonte`,
    executa ESSE texto no lugar do arquivo — e assim que o mutante nasce."""
    with mock.patch.dict(os.environ, {"WIKI_ROOT": str(raiz)}):
        loader = SourceFileLoader("check_cache_reserve_gatilho_teste", str(FERRAMENTA))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        modulo = importlib.util.module_from_spec(spec)
        if fonte is None:
            loader.exec_module(modulo)
        else:
            modulo.__file__ = str(FERRAMENTA)
            exec(compile(fonte, str(FERRAMENTA), "exec"), modulo.__dict__)
    return modulo


def roda(modulo, argv, ler_vivo=None):
    modulo.LER_VIVO = ler_vivo or vivo("off")
    limpo = {k: v for k, v in os.environ.items() if not k.startswith("CLOUDFLARE_")}
    buf = io.StringIO()
    with mock.patch.dict(os.environ, limpo, clear=True), \
            contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        rc = modulo.main(argv)
    saida = buf.getvalue()
    rel = json.loads(saida) if "--json" in argv and saida.strip().startswith("{") else None
    return rc, saida, rel


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = raiz_temporaria()
        self.baseline = self.raiz / "data" / "ops" / "cache_baseline_daily.jsonl"

    def tearDown(self):
        shutil.rmtree(self.raiz, ignore_errors=True)

    def serie(self, razoes_por_dia, misses=50):
        """razoes_por_dia: lista (um item por dia) de razao aplicada aos tres bots,
        ou dict bot->razao."""
        linhas = []
        for dia, r in zip(DIAS, razoes_por_dia):
            travessias = r if isinstance(r, dict) else {b: r for b in BOTS}
            linhas.append(linha_baseline(dia, travessias, misses=misses))
        grava_jsonl(self.baseline, linhas)


class Gatilho(Base):
    def test_abaixo_do_limiar_mantem_desligado(self):
        self.serie([0.01, 0.03, 0.02])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(rel["veredito"], "manter desligado")
        self.assertFalse(rel["regra_1"]["atingida"])
        self.assertFalse(rel["regra_2"]["atingida"])
        self.assertEqual([l["fonte"] for l in rel["linhas"]], ["baseline"] * 3)

    def test_acima_tres_dias_consecutivos_liga_e_nomeia_o_bot(self):
        self.serie([{"perplexitybot": 0.40, "oai-searchbot": 0.01, "bingbot": 0.01},
                    {"perplexitybot": 0.30, "oai-searchbot": 0.01, "bingbot": 0.01},
                    {"perplexitybot": 0.06, "oai-searchbot": 0.01, "bingbot": 0.01}])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 1, saida)
        self.assertEqual(rel["veredito"], "LIGAR")
        self.assertEqual(rel["regra_1"]["bots_atingidos"], ["perplexitybot"])
        self.assertIn("perplexitybot", rel["motivo"])

    def test_exatamente_no_limiar_nao_e_acima(self):
        self.serie([0.05, 0.05, 0.05])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)

    def test_dois_acima_um_abaixo_nao_liga_e_o_mutante_sem_consecutivos_liga(self):
        """2 dias acima + 1 abaixo = manter. PROVA POR MUTACAO: trocar all() por
        any() no guarda faz o MESMO cenario virar LIGAR."""
        self.serie([0.40, 0.30, 0.01])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(rel["veredito"], "manter desligado")

        fonte = FERRAMENTA.read_text(encoding="utf-8")
        guarda = "and all(v is not None and v > limiar for v in valores)"
        self.assertEqual(fonte.count(guarda), 1, "o guarda de consecutivos mudou de forma; ajuste o mutante")
        mutante = fonte.replace(guarda, "and any(v is not None and v > limiar for v in valores)")
        mod_m = carrega(self.raiz, fonte=mutante)
        rc_m, saida_m, rel_m = roda(mod_m, ARGS)
        print(f"\n  [mutacao] original: {rel['veredito']!r} (exit {rc}) | "
              f"mutante any(): {rel_m['veredito']!r} (exit {rc_m}) -- serie 40% / 30% / 1%")
        self.assertEqual(rc_m, 1, saida_m)
        self.assertEqual(rel_m["veredito"], "LIGAR", "o mutante sem exigencia de 3 consecutivos deveria LIGAR")

    def test_dia_faltando_no_meio_quebra_a_sequencia(self):
        grava_jsonl(self.baseline, [linha_baseline(DIAS[0], {b: 0.90 for b in BOTS}),
                                    linha_baseline(DIAS[2], {b: 0.90 for b in BOTS})])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(rel["veredito"], "manter desligado")
        self.assertIsNone(rel["linhas"][1]["fonte"])
        self.assertEqual(rel["regra_1"]["por_bot"]["perplexitybot"], [90.0, None, 90.0])

    def test_regra_2_misses_pre_head_liga_sozinha(self):
        self.serie([0.01, 0.01, 0.01], misses=300)  # > 2% de 10.141 = 202,82
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 1, saida)
        self.assertEqual(rel["veredito"], "LIGAR")
        self.assertTrue(rel["regra_2"]["atingida"])
        self.assertFalse(rel["regra_1"]["atingida"])
        self.assertAlmostEqual(rel["regra_2"]["limiar_absoluto"], 202.82, places=2)

    def test_regra_2_dois_dias_nao_liga(self):
        grava_jsonl(self.baseline, [linha_baseline(DIAS[0], {b: 0.01 for b in BOTS}, misses=300),
                                    linha_baseline(DIAS[1], {b: 0.01 for b in BOTS}, misses=300),
                                    linha_baseline(DIAS[2], {b: 0.01 for b in BOTS}, misses=10)])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)

    def test_ultima_linha_por_dia_da_baseline_e_a_que_vale(self):
        """A baseline e append idempotente: uma regravacao do mesmo dia vem depois."""
        grava_jsonl(self.baseline, [linha_baseline(d, {b: 0.90 for b in BOTS}) for d in DIAS])
        grava_jsonl(self.baseline, [linha_baseline(DIAS[2], {b: 0.01 for b in BOTS})])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(rel["regra_1"]["por_bot"]["bingbot"], [90.0, 90.0, 1.0])

    def test_texto_humano_traz_tabela_e_veredito(self):
        self.serie([0.40, 0.30, 0.06])
        mod = carrega(self.raiz)
        rc, saida, _ = roda(mod, ["--ate", "2026-09-08", "--dias", "3"])
        self.assertEqual(rc, 1, saida)
        self.assertIn("VEREDITO: LIGAR", saida)
        self.assertIn("purgas_tudo", saida)
        self.assertIn("2026-09-06", saida)
        self.assertIn("apply-cache-reserve --on --dry-run", saida)


class SemSerie(Base):
    def test_sem_baseline_e_sem_series_brutas_sai_2(self):
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 2, saida)
        self.assertIn("sem serie", rel["motivo"])
        self.assertIsNone(rel["veredito"])

    def test_sem_serie_mas_com_drift_sai_1(self):
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertTrue(rel["drift"])


def linha_borda(dia, bot, sampled):
    """Linha v4 do ledger da borda que passa em edgetelemetry.avaliar_linha."""
    return {"schema_version": "edge_bot_agents_daily_v4", "date": dia, "agent_key": bot,
            "authenticity": "cloudflare_verified_bot_category", "function": "search",
            "requests_estimated": sampled, "requests_sampled": sampled,
            "requests_sampled_cloudflare_verified": sampled, "requests_sampled_ip_range": 0,
            "requests_estimated_cloudflare_verified": sampled, "requests_estimated_ip_range": 0,
            "requests_estimated_unverified_ua": 0, "requests_sampled_unverified_ua": 0,
            "requests_local_verification": 0, "sampled_dataset": True, "query_truncated": False,
            "countries": {}, "countries_unverified_ua": {}, "verified_bot_categories": {},
            "user_agent_samples": [], "window_start": f"{dia}T00:00:00Z", "window_end": f"{dia}T23:59:59Z"}


def linha_origem(dia, bot, autenticas):
    return {"schema_version": "origin_bot_traffic_daily_v3", "date": dia, "agent_key": bot,
            "requests": autenticas, "requests_authentic": autenticas, "requests_forged": 0,
            "requests_unverifiable": 0, "summable": True, "verification_method": "ip_range"}


class Fallback(Base):
    def test_calcula_da_ultima_linha_e_nao_da_soma_cumulativa(self):
        """Ledger da borda e CUMULATIVO: 60 depois 100 no mesmo dia = 100 no dia.
        Origem 8: ultima linha => 8,0% (> 5, LIGAR); soma bruta => 8/160 = 5,0%
        (nao acima de 5, manter). A fixture separa os dois caminhos."""
        borda = self.raiz / "data" / "ops" / "edge_bot_agents_daily.jsonl"
        origem = self.raiz / "data" / "ops" / "origin_bot_traffic_daily.jsonl"
        for dia in DIAS:
            grava_jsonl(borda, [linha_borda(dia, "bingbot", 60), linha_borda(dia, "bingbot", 100)])
            grava_jsonl(origem, [linha_origem(dia, "bingbot", 5), linha_origem(dia, "bingbot", 3)])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 1, saida)
        self.assertEqual(rel["veredito"], "LIGAR")
        self.assertEqual([l["fonte"] for l in rel["linhas"]], ["calculado"] * 3)
        b = rel["linhas"][0]["travessia"]["bingbot"]
        self.assertEqual(b["borda"], 100)
        self.assertEqual(b["origem"], 8)
        self.assertEqual(b["travessia_pct"], 8.0)
        # Sem baseline nao ha misses_pre_head: a regra 2 fica n/d, nunca inventada.
        self.assertEqual(rel["regra_2"]["valores"], [None, None, None])
        self.assertFalse(rel["regra_2"]["atingida"])

    def test_baseline_tem_precedencia_sobre_o_calculo(self):
        borda = self.raiz / "data" / "ops" / "edge_bot_agents_daily.jsonl"
        origem = self.raiz / "data" / "ops" / "origin_bot_traffic_daily.jsonl"
        for dia in DIAS:
            grava_jsonl(borda, [linha_borda(dia, "bingbot", 100)])
            grava_jsonl(origem, [linha_origem(dia, "bingbot", 90)])
        grava_jsonl(self.baseline, [linha_baseline(DIAS[2], {b: 0.01 for b in BOTS})])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual([l["fonte"] for l in rel["linhas"]], ["calculado", "calculado", "baseline"])
        self.assertEqual(rel["regra_1"]["por_bot"]["bingbot"], [90.0, 90.0, 1.0])

    def test_borda_zero_e_nao_mensuravel_sem_divisao_por_zero(self):
        borda = self.raiz / "data" / "ops" / "edge_bot_agents_daily.jsonl"
        origem = self.raiz / "data" / "ops" / "origin_bot_traffic_daily.jsonl"
        for dia in DIAS:
            grava_jsonl(borda, [linha_borda(dia, "perplexitybot", 0)])
            grava_jsonl(origem, [linha_origem(dia, "perplexitybot", 40)])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS)
        self.assertEqual(rc, 0, saida)
        self.assertEqual(rel["linhas"][0]["travessia"]["perplexitybot"]["status"], "nao_mensuravel")


class Drift(Base):
    def test_vivo_on_sem_ledger_e_drift(self):
        self.serie([0.01, 0.01, 0.01])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertTrue(rel["drift"])
        self.assertIn("DRIFT", rel["drift_motivo"])
        self.assertNotIn("DESATUALIZADO", rel["drift_motivo"])
        # O veredito do gatilho continua sendo calculado e impresso.
        self.assertEqual(rel["veredito"], "manter desligado")

    def test_vivo_on_com_linha_da_ferramenta_e_canonico_desatualizado(self):
        self.serie([0.01, 0.01, 0.01])
        grava_jsonl(self.raiz / "data" / "ops" / "edge_rule_apply.jsonl", [
            {"schema_version": "edge_rule_apply_v1", "aplicado_em": "2026-09-10T10:00:00+00:00",
             "zona": "z", "fase": "cache_reserve", "evento": "intencao", "ferramenta": "tools/apply-cache-reserve",
             "motivo": "gatilho atingido", "valor_antes": "off", "valor_pretendido": "on",
             "regras_antes": [{"value": "off"}], "regras_depois_pretendidas": [{"value": "on"}]},
            {"schema_version": "edge_rule_apply_v1", "aplicado_em": "2026-09-10T10:00:01+00:00",
             "zona": "z", "fase": "cache_reserve", "evento": "resultado", "operacao": "PATCH",
             "valor_pretendido": "on", "http_status": 200, "success": True, "errors": [],
             "result": {"value": "on"}}])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertTrue(rel["drift"])
        self.assertIn("DESATUALIZADO", rel["drift_motivo"])
        self.assertIn("gatilho atingido", rel["drift_motivo"])
        self.assertNotIn("DRIFT:", rel["drift_motivo"])

    def test_intencao_orfa_por_patch_recusado_nao_explica_o_painel(self):
        """O primeiro evento real provavel numa zona Free: a ferramenta TENTA
        ligar, a API recusa ('A paid Cache Reserve plan is required'), o ledger
        fica com intencao(on) + resultado(success:false). Se DEPOIS alguem ligar
        pelo painel, o vivo 'on' NAO esta explicado: e DRIFT, nao 'canonico
        desatualizado'."""
        self.serie([0.01, 0.01, 0.01])
        grava_jsonl(self.raiz / "data" / "ops" / "edge_rule_apply.jsonl", [
            {"schema_version": "edge_rule_apply_v1", "aplicado_em": "2026-09-10T10:00:00+00:00",
             "zona": "z", "fase": "cache_reserve", "evento": "intencao", "ferramenta": "tools/apply-cache-reserve",
             "motivo": "gatilho atingido", "valor_antes": "off", "valor_pretendido": "on",
             "regras_antes": [{"value": "off"}], "regras_depois_pretendidas": [{"value": "on"}]},
            {"schema_version": "edge_rule_apply_v1", "aplicado_em": "2026-09-10T10:00:01+00:00",
             "zona": "z", "fase": "cache_reserve", "evento": "resultado", "operacao": "PATCH",
             "valor_pretendido": "on", "http_status": 400, "success": False,
             "errors": ["Cache Reserve requires a paid plan"], "result": None}])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertTrue(rel["drift"])
        self.assertIn("DRIFT:", rel["drift_motivo"])
        self.assertNotIn("DESATUALIZADO", rel["drift_motivo"])

    def test_ligou_com_sucesso_e_depois_falhou_ao_desligar_continua_explicado(self):
        self.serie([0.01, 0.01, 0.01])
        grava_jsonl(self.raiz / "data" / "ops" / "edge_rule_apply.jsonl", [
            {"fase": "cache_reserve", "evento": "intencao", "ferramenta": "tools/apply-cache-reserve",
             "motivo": "gatilho", "valor_pretendido": "on", "aplicado_em": "2026-09-10T10:00:00+00:00"},
            {"fase": "cache_reserve", "evento": "resultado", "operacao": "PATCH", "valor_pretendido": "on",
             "success": True, "result": {"value": "on"}},
            {"fase": "cache_reserve", "evento": "intencao", "ferramenta": "tools/apply-cache-reserve",
             "motivo": "rollback", "valor_pretendido": "off", "aplicado_em": "2026-09-11T10:00:00+00:00"},
            {"fase": "cache_reserve", "evento": "resultado", "operacao": "PATCH", "valor_pretendido": "off",
             "success": False, "result": None},
            {"fase": "cache_reserve", "evento": "resultado", "operacao": "POST cache_reserve_clear",
             "success": True, "result": {"state": "In-progress"}}])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertIn("DESATUALIZADO", rel["drift_motivo"])
        self.assertIn("motivo: gatilho", rel["drift_motivo"])

    def test_linha_de_outra_fase_nao_explica(self):
        self.serie([0.01, 0.01, 0.01])
        grava_jsonl(self.raiz / "data" / "ops" / "edge_rule_apply.jsonl", [
            {"schema_version": "edge_rule_apply_v1", "fase": "http_request_cache_settings",
             "regras_antes": [], "regras_depois_pretendidas": [{"value": "on"}]}])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo("on"))
        self.assertEqual(rc, 1, saida)
        self.assertIn("DRIFT", rel["drift_motivo"])

    def test_sem_credencial_nao_e_drift_e_o_disco_decide(self):
        self.serie([0.40, 0.30, 0.06])
        mod = carrega(self.raiz)
        rc, saida, rel = roda(mod, ARGS, ler_vivo=vivo_indisponivel)
        self.assertEqual(rc, 1, saida)  # pela regra 1, nao por drift
        self.assertFalse(rel["drift"])
        self.assertFalse(rel["vivo"]["verificado"])
        self.assertEqual(rel["veredito"], "LIGAR")

    def test_sem_vivo_nao_chama_a_api(self):
        self.serie([0.01, 0.01, 0.01])
        mod = carrega(self.raiz)

        def explode(*a, **k):
            raise AssertionError("--sem-vivo nao pode chamar LER_VIVO")
        rc, saida, rel = roda(mod, ARGS + ["--sem-vivo"], ler_vivo=explode)
        self.assertEqual(rc, 0, saida)
        self.assertFalse(rel["vivo"]["verificado"])


class HarnessQuebrado(unittest.TestCase):
    def test_canonico_ausente_sai_2(self):
        raiz = raiz_temporaria(com_canonico=False)
        try:
            mod = carrega(raiz)
            rc, saida, rel = roda(mod, ARGS)
        finally:
            shutil.rmtree(raiz, ignore_errors=True)
        self.assertEqual(rc, 2, saida)
        self.assertIn("canonico", rel["motivo"])


class Canonico(unittest.TestCase):
    def test_gatilho_com_os_numeros_da_decisao(self):
        dados = json.loads(CANONICO.read_text(encoding="utf-8"))
        g = dados["gatilho_para_ligar"]
        self.assertEqual(sorted(g["regra_1"]["bots"]), sorted(BOTS))
        self.assertEqual(g["regra_1"]["limiar_pct"], 5.0)
        self.assertEqual(g["regra_1"]["dias_consecutivos"], 3)
        self.assertEqual(g["regra_2"]["limiar_pct_do_acervo"], 2.0)
        self.assertEqual(g["regra_2"]["acervo_referencia"], 10141)
        self.assertEqual(g["regra_2"]["dias_consecutivos"], 3)
        self.assertEqual(dados["valor_esperado"], "off")


if __name__ == "__main__":
    unittest.main(verbosity=2)
