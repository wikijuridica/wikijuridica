#!/usr/bin/env python3
"""Testes de tools/run-gates-rotativos — o runner que acabou com os 351 gates cegos.

TODO teste roda OFFLINE e sem executar gate nenhum: a lista de gates e a execução
são substituídas por dublês, e o que se exercita é a DECISÃO (quem roda, em que
ordem, dentro de qual orçamento) e o LEDGER (que é o que prova a cobertura).

O PESO ESTÁ NAS DUAS PROPRIEDADES QUE, SE QUEBRAREM, DEVOLVEM A CEGUEIRA:

  1. A FILA ANDA. Foi o defeito do primeiro desenho, pego na medição de
     2026-09-05: 87 gates casam o padrão de risco e só eles já estouram o
     orçamento, então "fixos primeiro, resto se sobrar" nunca chegava ao gate 88.
     A reserva da fila existe para isso, e o teste 3 cobra o efeito dela.
  2. O MAIS ANTIGO SOBE. Sem essa ordem, um gate que não coube ontem também não
     cabe hoje, e a "rotação" é uma lista que roda sempre o mesmo prefixo.

E o que nunca pode virar exit 0: lista de gates vazia ou pequena demais é INFRA
QUEBRADA. Devolver 0 ali seria o mesmo buraco que este runner veio fechar — um
gate que não rodou contado como gate que passou.

Rodar:
    python3 tools/test_run_gates_rotativos.py
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "run-gates-rotativos"


def carrega():
    """Importa o script sem extensão .py.

    spec_from_file_location devolve loader None para arquivo sem extensão
    conhecida; SourceFileLoader resolve, e é o mesmo caminho que as outras
    bancadas deste diretório usam.
    """
    spec = importlib.util.spec_from_loader("rotativos", SourceFileLoader("rotativos", str(ALVO)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Bancada(unittest.TestCase):
    def setUp(self):
        self.mod = carrega()
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="gates-rotativos-"))
        self.ledger = self.tmp / "gates_rotativos.jsonl"
        self.mod.LEDGER = self.ledger

    def escreve_ledger(self, linhas):
        with self.ledger.open("w", encoding="utf-8") as f:
            for l in linhas:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")

    # --- 1. a classificação: risco não espera a vez -------------------------

    def test_1_assunto_de_risco_e_fixo_e_fechamento_fica_de_fora(self):
        fixo = ["legal-oab-compliance", "sitemap-fidelity", "social-csp",
                "social-isolation", "ponte-editorial-sem-autoria", "crawler-identity-bart"]
        for nome in fixo:
            self.assertTrue(self.mod.SEMPRE.search(nome.lower()),
                            "%s deveria ser fixo (risco juridico/publicacao/identidade)" % nome)
        for nome in ("redesocial-entrega-final", "p0-cycle-close-indexable-10k"):
            self.assertTrue(self.mod.FECHAMENTO.search(nome.lower()),
                            "%s e gate de fechamento e nao entra na rodada diaria" % nome)
        # e um gate comum não pode virar fixo por acidente de substring
        self.assertFalse(self.mod.SEMPRE.search("agent-context-ledger"))

    # --- 2. o mais antigo sobe na fila --------------------------------------

    def test_2_idade_ordena_a_fila_e_nunca_executado_vem_primeiro(self):
        hoje = datetime.date(2026, 9, 5)
        ultimo = {"rodou-ontem": "2026-09-04", "rodou-ha-um-mes": "2026-08-06"}
        self.assertEqual(self.mod.idade("rodou-ontem", ultimo, hoje), 1)
        self.assertEqual(self.mod.idade("rodou-ha-um-mes", ultimo, hoje), 30)
        # nunca executado tem de vencer QUALQUER idade real, senão um gate novo
        # entra no fim da fila e demora um ciclo inteiro para ser exercitado
        self.assertGreater(self.mod.idade("nunca-rodou", ultimo, hoje), 30)
        # data corrompida no ledger não pode ser lida como "rodou hoje"
        self.assertGreater(self.mod.idade("x", {"x": "data-torta"}, hoje), 30)

    # --- 2b. o empate de idade não pode ser desfeito pelo alfabeto ---------

    def test_2b_empate_de_idade_nao_e_desfeito_pelo_alfabeto(self):
        """Gate NUNCA executado tem idade 10.000 — todos empatados.

        Enquanto o desempate era `n` (o nome), o fim do alfabeto perdia todo
        dia; com o orçamento estourando em toda rodada, "perder todo dia" é
        "nunca rodar". Medido no ledger em 2026-09-10, sobre 8 rodadas e 358
        gates: 309 rodaram ao menos uma vez, 51 NUNCA — e os 51 são um sufixo
        alfabético contínuo, de `redesocial-entrega-final` a
        `zizmor-workflow-security`, incluindo `seo`, `v2-cross-shard-collision`,
        `sem-dado-pessoal-em-git` e os onze `social-*`.
        """
        hoje = datetime.date(2026, 9, 10)
        nomes = ["zzz-ultimo", "aaa-primeiro", "mmm-meio", "sss-quase-fim"]
        # A ASSERÇÃO É SOBRE `ordem_da_fila`, NÃO SOBRE `desempate`. A primeira
        # versão deste caso ordenava por `desempate` direto e um mutante que
        # devolvia `ordem` ao alfabeto SOBREVIVIA — o teste media o ajudante, e
        # o defeito mora na decisão. É o mesmo erro que este repositório já
        # pagou como "teste que reimplementa não testa".
        ordenado = sorted(nomes, key=lambda n: self.mod.ordem_da_fila(n, {}, hoje))
        self.assertNotEqual(
            ordenado, sorted(nomes),
            "o desempate voltou a ser alfabetico: o fim do alfabeto nunca roda")

    def test_2c_o_desempate_e_estavel_no_dia_e_muda_entre_dias(self):
        """Reprodutível dentro da rodada, rotativo entre rodadas.

        As duas metades importam: sem estabilidade no dia o ledger deixa de ser
        auditável (dois replays da mesma rodada dariam ordens diferentes); sem
        mudança entre dias o sufixo de ontem continua sendo o sufixo de hoje.
        """
        nomes = ["zzz-ultimo", "aaa-primeiro", "mmm-meio", "sss-quase-fim"]
        dia = datetime.date(2026, 9, 10)
        outro = datetime.date(2026, 9, 11)
        ordem_dia = sorted(nomes, key=lambda n: self.mod.ordem_da_fila(n, {}, dia))
        self.assertEqual(ordem_dia, sorted(nomes, key=lambda n: self.mod.ordem_da_fila(n, {}, dia)),
                         "a ordem tem de ser a mesma em dois replays do mesmo dia")
        self.assertNotEqual(ordem_dia, sorted(nomes, key=lambda n: self.mod.ordem_da_fila(n, {}, outro)),
                            "a ordem tem de mudar de um dia para o outro, senao nada rotaciona")

    def test_2d_idade_continua_dominando_o_desempate(self):
        """O sorteio decide EMPATE — nunca inverte idades diferentes."""
        hoje = datetime.date(2026, 9, 10)
        ultimo = {"rodou-ontem": "2026-09-09"}
        # "rodou-ontem" tem idade 1; "nunca-rodou" tem 10.000 e vem antes,
        # qualquer que seja o sorteio
        self.assertLess(self.mod.ordem_da_fila("nunca-rodou", ultimo, hoje),
                        self.mod.ordem_da_fila("rodou-ontem", ultimo, hoje))

    # --- 3. a decisão de orçamento, exercitada em main() --------------------

    def roda_main(self, orcamento, ultimo=None, fixos=90, comuns=10,
                  custo_fixo=20, custo_comum=1, custo_build=3, morre_em=None,
                  custos=None):
        """Executa main() de verdade, com a lista de gates e a execução dubladas.

        NÃO recalcula fórmula nenhuma — é essa a diferença que importa. A versão
        anterior deste teste refazia a conta da reserva por conta própria e nunca
        chamava main(): apagar o bloco do orçamento do script deixava os nove
        testes verdes. Aqui, o que se mede é o caminho que decide.

        Nada dorme e nada executa: o relógio é injetado por `mod.agora` e cada
        gate dublado o avança pelo custo que se quer simular.

        O DUBLÊ HONRA `--max-duration`, e isso não é capricho: desde que a
        rodada passou a executar LOTES num processo só, quem impede o lote de
        estourar a fatia dos fixos e engolir a reserva da fila é justamente o
        orçamento que `cmd/check` aplica gate a gate (`runCheckWithBudget`).
        Um dublê que ignorasse a flag deixaria passar um runner que só funciona
        no papel. O gate em que o orçamento estoura sai com `status=fail`,
        exatamente como o binário faz; os seguintes do lote não emitem linha
        nenhuma, porque não chegaram a rodar.

        `morre_em` simula o processo que MORRE dentro de um gate (pânico, OOM):
        emite `status=start` e nada mais. O gate tem de sair como FALHA.
        """
        nomes = (["legal-a%02d" % i for i in range(1, fixos + 1)]
                 + ["alfa-%02d" % i for i in range(1, comuns + 1)])
        self.mod.lista_de_gates = lambda binario: nomes
        if ultimo:
            self.escreve_ledger([{"data": d, "gates": [n]} for n, d in sorted(ultimo.items())])

        relogio = [datetime.datetime(2026, 9, 5, 12, 0, 0)]
        self.mod.agora = lambda: relogio[0]

        chamados = []

        class Resultado:
            def __init__(self, returncode=0, stdout="", stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        def custo_de(nome):
            if custos and nome in custos:
                return custos[nome]
            return custo_fixo if nome.startswith("legal-") else custo_comum

        def run_dublado(cmd, **kwargs):
            if "build" in cmd:
                # a compilacao unica da rodada
                relogio[0] += datetime.timedelta(seconds=custo_build)
                return Resultado()
            lote = cmd[cmd.index("--checks") + 1].split(",")
            teto = int(cmd[cmd.index("--max-duration") + 1].rstrip("s"))
            timing, saida = [], []
            gasto_no_lote = 0
            codigo = 0
            for nome in lote:
                if gasto_no_lote >= teto:
                    break  # "check budget exceeded before X": nem chegou a rodar
                chamados.append(nome)
                timing.append("TIMING check=%s status=start" % nome)
                if nome == morre_em:
                    # processo morre aqui: sem linha de fim, sem os gates seguintes
                    return Resultado(2, "\n".join(saida),
                                     "\n".join(timing) + "\npanic: gate estourou")
                custo = custo_de(nome)
                relogio[0] += datetime.timedelta(seconds=custo)
                gasto_no_lote += custo
                estourou = gasto_no_lote > teto
                estado = "fail" if estourou else "pass"
                timing.append("TIMING check=%s status=%s duration_ms=%d"
                              % (nome, estado, custo * 1000))
                if estourou:
                    codigo = 1
                    saida.append("check budget exceeded during %s: max_duration=%ds" % (nome, teto))
                    break
                saida.append("%s: pass" % nome)
            return Resultado(codigo, "\n".join(saida), "\n".join(timing))

        # Substitui o ATRIBUTO do módulo sob teste, nunca subprocess.run global:
        # um patch global vazaria para o resto da bancada.
        class ShimSubprocess:
            run = staticmethod(run_dublado)
            # o runner captura o pendurado para nao perder o ledger da rodada
            TimeoutExpired = subprocess.TimeoutExpired

        self.mod.subprocess = ShimSubprocess
        sys.argv = ["run-gates-rotativos", "--orcamento", str(orcamento)]
        codigo = self.mod.main()
        ultima = self.ledger.read_text(encoding="utf-8").strip().splitlines()[-1]
        return codigo, chamados, json.loads(ultima)

    def test_2e_main_nao_executa_o_prefixo_alfabetico_quando_todos_empatam(self):
        """A decisão tem de valer NO CAMINHO, não só na função isolada.

        Os casos 2b-2d exercitam `ordem_da_fila` direto, e um mutante que
        devolvesse a ordenação de `main()` ao alfabeto SOBREVIVIA a eles: a
        função certa continuava certa, e o chamador é que voltava a errar. Aqui
        a asserção é sobre `chamados` — quem de fato rodou —, com todos os gates
        empatados em "nunca executado" e orçamento que só comporta uma parte.
        """
        codigo, chamados, _ = self.roda_main(200)
        self.assertEqual(codigo, 0)
        fixos_chamados = [n for n in chamados if n.startswith("legal-")]
        self.assertTrue(fixos_chamados, "nenhum fixo rodou: o cenario nao exercita a ordem")
        # com desempate alfabetico, os que rodam sao SEMPRE legal-a01, a02, ...
        prefixo_alfabetico = ["legal-a%02d" % i for i in range(1, len(fixos_chamados) + 1)]
        self.assertNotEqual(
            fixos_chamados, prefixo_alfabetico,
            "main() executou exatamente o prefixo alfabetico: o fim da lista "
            "nunca roda, que e o defeito medido em 2026-09-10 (51 gates cegos)")

    def test_3_reserva_da_fila_garante_progresso_mesmo_com_fixos_demais(self):
        # O defeito medido em 2026-09-05: os fixos sozinhos consomem mais que a
        # rodada. Sem a reserva, ZERO gates da fila rodam e a rotação não
        # rotaciona. 90 fixos a 20 s são 1800 s para um orçamento de 200.
        codigo, chamados, registro = self.roda_main(200)
        self.assertEqual(codigo, 0)
        self.assertTrue([n for n in chamados if n.startswith("alfa-")],
                        "sem reserva a fila nunca anda: nenhum gate comum rodou")
        self.assertGreater(registro["fixos_fora_do_orcamento"], 0,
                           "fixo que nao coube tem de ser CONTADO, nao escondido")
        self.assertEqual(registro["gates_registrados"], 100)

    def test_3b_o_fixo_mais_antigo_sobe_e_nao_so_o_da_fila(self):
        # A metade que o commit 6d51e48f declarou resolvida e não estava: a
        # ordem por idade valia só para a fila. Com 90 fixos e espaço para ~6,
        # sem ordenar os fixos os MESMOS 6 primeiros de `Names` rodariam todo
        # dia e os outros 84 nunca — inclusive um gate de risco jurídico.
        ultimo = {"legal-a%02d" % i: "2026-09-04" for i in range(1, 91)}
        ultimo["legal-a90"] = "2026-08-06"  # 30 dias sem rodar: tem de ser o 1º
        codigo, chamados, _ = self.roda_main(200, ultimo=ultimo)
        self.assertEqual(codigo, 0)
        self.assertEqual(chamados[0], "legal-a90",
                         "o fixo ha mais tempo sem rodar tem de abrir a rodada; "
                         "sem fixos.sort ele nunca entra. Rodou: %s" % chamados[:8])

    # --- 4. o ledger é o que prova a cobertura ------------------------------

    def test_4_historico_le_a_ultima_execucao_de_cada_gate(self):
        self.escreve_ledger([
            {"data": "2026-09-01", "gates": ["a", "b"]},
            {"data": "2026-09-04", "gates": ["b", "c"]},
        ])
        h = self.mod.historico()
        self.assertEqual(h["a"], "2026-09-01")
        self.assertEqual(h["b"], "2026-09-04", "a data MAIS RECENTE de b tem de vencer")
        self.assertEqual(h["c"], "2026-09-04")

    def test_5_linha_torta_nao_apaga_o_historico(self):
        self.ledger.write_text(
            '{"data": "2026-09-01", "gates": ["a"]}\n'
            'isto nao e json\n'
            '{"data": "2026-09-04", "gates": ["b"]}\n', encoding="utf-8")
        h = self.mod.historico()
        self.assertEqual(h.get("a"), "2026-09-01")
        self.assertEqual(h.get("b"), "2026-09-04")

    def test_6_ledger_ausente_nao_e_erro(self):
        self.assertEqual(self.mod.historico(), {},
                         "primeira execucao nao tem ledger, e isso nao e falha")

    # --- 7. NÃO RODOU tem de ser 2, nunca 0 ---------------------------------

    def test_7_lista_pequena_demais_nao_rodou(self):
        self.mod.compila_binario = lambda: self.tmp / "check"
        self.mod.lista_de_gates = lambda binario: ["um", "dois"]
        sys.argv = ["run-gates-rotativos"]
        self.assertEqual(self.mod.main(), 2,
                         "lista implausivel e infra quebrada: exit 2, nunca 0")

    def test_8_falha_ao_listar_nao_rodou(self):
        def explode(binario):
            raise RuntimeError("toolchain ausente")
        self.mod.compila_binario = lambda: self.tmp / "check"
        self.mod.lista_de_gates = explode
        sys.argv = ["run-gates-rotativos"]
        self.assertEqual(self.mod.main(), 2)

    def test_8b_compilacao_que_falha_nao_vira_rodada_verde(self):
        # Arvore que nao compila e INFRA: exit 2. Se virasse exit 0 com zero
        # gates, a bancada diaria acenderia verde no dia em que NENHUM gate
        # rodou -- a cegueira exata que este runner veio fechar.
        def explode():
            raise RuntimeError("compilacao de ./cmd/check falhou: too many return values")
        self.mod.compila_binario = explode
        sys.argv = ["run-gates-rotativos"]
        self.assertEqual(self.mod.main(), 2)

    # --- 10. o custo do invólucro: lote e duração medida --------------------

    def test_10_gates_vao_em_lote_num_processo_so(self):
        # A CAUSA MEDIDA em 2026-09-10: um `go run` por gate custava ~4 s de
        # relink que nao medem nada -- 34% do orcamento da rodada de 09-07, e o
        # buraco por onde 9 gates FIXOS escaparam. Um gate por processo tambem
        # joga fora o RunContext (build publico, corpus v2) a cada gate.
        # Se alguem voltar a chamar um gate por processo, este teste reprova.
        chamadas = []
        original = self.mod.executa_lote

        def espia(binario, lote, teto):
            chamadas.append(list(lote))
            return original(binario, lote, teto)

        self.mod.executa_lote = espia
        codigo, chamados, _ = self.roda_main(1200, fixos=60, comuns=10, custo_fixo=1)
        self.assertTrue(chamadas, "nenhum lote executado")
        self.assertGreater(max(len(l) for l in chamadas), 1,
                           "os gates voltaram a rodar um por processo: %s" % chamadas[:3])
        self.assertLessEqual(max(len(l) for l in chamadas), self.mod.TAM_LOTE)
        self.assertEqual(codigo, 0)

    def test_11_ledger_grava_duracao_por_gate(self):
        # Sem duracao por gate, "quem esta caro" so se respondia com cronometro
        # na mao, e o resumo mandava subir o orcamento sem dizer para onde o
        # tempo foi.
        _, chamados, registro = self.roda_main(1200, fixos=60, comuns=10,
                                               custo_fixo=7, custo_comum=2)
        duracoes = registro["duracoes_s"]
        self.assertEqual(set(duracoes), set(registro["gates"]),
                         "todo gate executado tem de ter duracao registrada")
        self.assertEqual(duracoes["legal-a01"], 7)
        self.assertEqual(duracoes["alfa-01"], 2)
        self.assertIn("build_s", registro)

    def test_12_gate_que_mata_o_processo_e_FALHA_nao_silencio(self):
        # Comecou (status=start) e nao terminou: o processo morreu dentro dele.
        # Contar isso como "nao executou" faria o gate subir pela idade, matar o
        # processo de novo amanha e NUNCA aparecer como falha.
        codigo, chamados, registro = self.roda_main(1200, fixos=60, comuns=10,
                                                    custo_fixo=1,
                                                    morre_em="legal-a03")
        self.assertEqual(codigo, 1, "gate que mata o processo tem de reprovar a rodada")
        self.assertIn("legal-a03", registro["gates"],
                      "o gate que matou o processo tem de constar como executado e reprovado")

    def test_13_lote_respeita_o_orcamento_e_a_fila_anda(self):
        # O risco novo que o lote introduz: um lote grande estourando a fatia
        # dos fixos e engolindo a reserva da fila. Quem impede e o
        # --max-duration passado ao processo do lote.
        codigo, chamados, registro = self.roda_main(200, custo_fixo=20, custo_comum=1)
        self.assertTrue([n for n in chamados if n.startswith("alfa-")],
                        "o lote comeu a reserva da fila: nenhum gate comum rodou")
        self.assertLessEqual(registro["gasto_s"], 200 + self.mod.TETO_POR_GATE,
                             "a rodada estourou o orcamento alem do teto de um lote")

    def test_14_gate_caro_nao_e_comecado_sem_caber(self):
        # O DESPERDICIO MEDIDO em 2026-09-10: 450 s dos 1200 s da rodada (37%)
        # foram gastos em gates COMECADOS sem caber. Corte nao devolve veredito:
        # o gate roda de novo do zero amanha e o tempo some. Com a duracao
        # medida no ledger, o empacotador nao comeca o que nao cabe.
        # legal-a01 tem de ser o MAIS ANTIGO, senao ele nem chega a vez e o
        # teste passaria pelo motivo errado (foi o que aconteceu na primeira
        # versao deste caso, pega por mutacao).
        self.escreve_ledger([
            {"data": "2026-08-01", "gates": ["legal-a01"], "duracoes_s": {"legal-a01": 500.0}},
            {"data": "2026-09-04", "gates": ["legal-a%02d" % i for i in range(2, 91)]},
        ])
        _, chamados, registro = self.roda_main(200, custo_fixo=20, custo_comum=1)
        self.assertNotIn("legal-a01", chamados,
                         "gate de 500s medidos nao pode ser comecado numa fatia de 120s")
        self.assertTrue([n for n in chamados if n.startswith("alfa-")],
                        "a fila tem de andar mesmo com um gate caro na frente")
        self.assertNotIn("legal-a01", registro["gates"])

    def test_15_estimativa_sai_da_medicao_mais_recente_do_ledger(self):
        self.escreve_ledger([
            {"data": "2026-09-01", "gates": ["x"], "duracoes_s": {"x": 90.0}},
            {"data": "2026-09-04", "gates": ["x", "y"], "duracoes_s": {"x": 12.0, "y": 3.0}},
        ])
        e = self.mod.estimativas()
        self.assertEqual(e["x"], 12.0, "vale a medicao mais recente, nao a primeira")
        self.assertEqual(e["y"], 3.0)
        self.assertNotIn("z", e, "gate sem medicao nao inventa custo")

    def test_16_dois_gates_caros_vao_em_lotes_separados(self):
        # MEDIDO em 2026-09-10: com 400 s restantes, dois gates de 180 s "cabem
        # no restante" mas NAO cabem no mesmo processo, que roda com
        # --max-duration 240s. O segundo era cortado aos 240 s e devolvia nada.
        # Empacotar contra o TETO DO LOTE poe cada um no seu e os dois entregam
        # veredito.
        self.escreve_ledger([
            {"data": "2026-08-01", "gates": ["legal-a01", "legal-a02"],
             "duracoes_s": {"legal-a01": 180.0, "legal-a02": 182.0}},
            {"data": "2026-09-04", "gates": ["legal-a%02d" % i for i in range(3, 91)]},
        ])
        lotes = []
        original = self.mod.executa_lote

        def espia(binario, lote, teto):
            lotes.append(list(lote))
            return original(binario, lote, teto)

        self.mod.executa_lote = espia
        _, chamados, registro = self.roda_main(1000, custo_fixo=180, custo_comum=1)
        self.assertIn("legal-a01", registro["gates"])
        self.assertIn("legal-a02", registro["gates"],
                      "o segundo gate caro foi cortado: o lote nao respeitou o teto. Lotes: %s"
                      % lotes[:3])
        self.assertNotIn(["legal-a01", "legal-a02"], lotes,
                         "dois gates de 180s nao podem dividir um lote de teto 240s")

    def test_17_corte_vira_piso_de_custo_e_nao_se_repete_na_mesma_rodada(self):
        # O gate cortado tem duracao medida (cmd/check imprime o TIMING antes de
        # abortar). Descarta-la fazia a rodada apostar de novo no mesmo gate --
        # `priority-controlled-promotion` foi cortado DUAS vezes em 2026-09-10.
        self.escreve_ledger([
            {"data": "2026-08-01", "gates": ["legal-a01"], "duracoes_s": {}},
            {"data": "2026-09-04", "gates": ["legal-a%02d" % i for i in range(2, 91)]},
        ])
        _, chamados, registro = self.roda_main(700, custo_fixo=300, custo_comum=1)
        cortados = registro["cortados_por_orcamento"]
        self.assertTrue(cortados, "o gate que estourou o teto do lote tem de constar como cortado")
        nome, piso = next(iter(cortados.items()))
        self.assertGreater(piso, 0, "corte sem piso de custo nao ensina nada a rodada seguinte")
        self.assertEqual(chamados.count(nome), 1,
                         "gate cortado nao pode ser tentado de novo na MESMA rodada: %s" % chamados[:6])

    def test_18_corte_pula_o_gate_e_a_rodada_continua(self):
        # MEDIDO em 2026-09-10: tratar corte como fim de grupo parou a rodada
        # aos 688 s de um orcamento de 1200 s -- 512 s de relogio ocioso com 320
        # gates esperando. O corte tira UM gate do dia, nunca o resto da lista.
        _, chamados, registro = self.roda_main(
            1200, fixos=60, comuns=10, custo_fixo=1, custo_comum=1,
            custos={"legal-a05": 400})
        self.assertIn("legal-a05", registro["cortados_por_orcamento"],
                      "o gate de 400s tinha de ser cortado pelo teto do lote")
        self.assertNotIn("legal-a05", registro["gates"], "cortado nao tem veredito")
        posteriores = [n for n in chamados if n.startswith("legal-a") and n > "legal-a05"]
        self.assertTrue(posteriores,
                        "a rodada parou no corte: nenhum gate depois dele rodou. Rodou: %s"
                        % chamados[:10])
        self.assertTrue([n for n in chamados if n.startswith("alfa-")],
                        "a fila tambem tem de andar depois de um corte nos fixos")

    # --- 9. o teto por gate existe e é menor que a rodada -------------------

    def test_9_teto_por_gate_impede_que_um_so_coma_a_rodada(self):
        # `p0-pipeline-integration` consumiu 4 minutos sozinho na medição de
        # 2026-09-05. Sem teto por gate, ele zera a fila todo dia.
        self.assertLess(self.mod.TETO_POR_GATE, self.mod.ORCAMENTO_PADRAO,
                        "o teto por gate tem de ser menor que a rodada inteira")
        self.assertGreater(self.mod.TETO_POR_GATE, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
