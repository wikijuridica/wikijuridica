#!/usr/bin/env python3
"""O oráculo devolve o veredito dos decisores REAIS — não uma segunda régua.

★ O QUE PRECISA SER VERDADE (e o que cada teste prova)

1. O motivo que o oráculo imprime é o motivo que `internal/v2ingest` emite,
   caractere por caractere. Se ele traduzisse, resumisse ou reimplementasse,
   viraria a sétima régua do repositório — exatamente o defeito que ele
   existe para matar.
2. O veredito de PUBLICAÇÃO vem do censo de severidade, que é quem
   `internal/v2publish.SelectPublishable` (v2publish.go:398) consulta.
3. Decisor que não roda NUNCA vira "passou". Falha de execução tem de
   interromper com exit 2, porque um oráculo que responde verde quando não
   mediu nada é pior que oráculo nenhum.
4. Página real e boa passa nos dois eixos (teste de FALSO POSITIVO sobre
   amostra do acervo, como manda a skill `rodar-gate`).

★ PROVA POR MUTAÇÃO

Os testes `test_mutante_*` aplicam a mutação a uma CÓPIA do oráculo, num
diretório temporário, e exigem que a asserção correspondente morra. O arquivo
do repositório nunca é tocado.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True  # SourceFileLoader + .pyc velho já cegou prova aqui

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ORACULO = RAIZ / "tools" / "oraculo-de-admissibilidade"


def carrega_oraculo(caminho: pathlib.Path):
    spec = importlib.util.spec_from_loader(
        "oraculo_sob_teste",
        importlib.machinery.SourceFileLoader("oraculo_sob_teste", str(caminho)))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def pagina_minima(intent: str, **sobrescritas) -> dict:
    """Uma página no formato do WRITING_SPEC §7, sem defeito proposital."""
    pagina = {
        "intent_id": intent,
        "title": "Garantia legal de produto durável: o prazo do CDC",
        "meta_description": "O que diz a lei sobre o prazo de reclamação por vício em produto durável, como ele é contado e o que fazer quando o reparo não vem.",
        "h1": "Prazo de reclamação por vício em produto durável",
        "opening": "A garantia legal é automática e independe de contrato: ela nasce da própria lei e acompanha todo produto colocado no mercado brasileiro.",
        "page_type": "verbete",
        "practice_area": "consumidor",
        "lane": "informativa",
        "word_count": 467,
        "sections": [
            {"heading": "O prazo que a lei fixa para o produto durável",
             "text": " ".join([
                 "O prazo de reclamação por vício aparente em produto durável é de noventa dias, contados da entrega efetiva.",
                 "A contagem muda quando o vício é oculto: nesse caso o prazo começa no momento em que o defeito se evidencia.",
                 "Essa distinção decide muitos casos concretos, porque o consumidor costuma descobrir o problema meses depois da compra.",
                 "A obrigação de sanar o vício alcança fornecedor e fabricante de forma solidária, e a escolha entre eles é do consumidor.",
             ] * 3)},
            {"heading": "O que fazer quando o fornecedor não repara no prazo",
             "text": " ".join([
                 "Passados trinta dias sem reparo, a lei abre três caminhos alternativos ao consumidor, à escolha dele.",
                 "São a substituição do produto, a devolução da quantia paga com correção e o abatimento proporcional do preço.",
                 "O registro da reclamação, com data e protocolo, é o que sustenta qualquer dos três caminhos depois.",
             ] * 4)},
        ],
        "faq": [{"q": "A garantia contratual substitui a legal?",
                 "a": "Não. A garantia contratual é complementar à legal e se soma a ela, nunca a reduz."}],
        "official_sources": [
            {
                "url": "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm",
                "name": "Lei 8.078/1990 (Código de Defesa do Consumidor), texto compilado",
                "anchor_claim": "art. 26, II e §3º",
                "verified_at": "2026-09-01T00:00:00Z",
                "http_status": 200,
            },
            {
                "url": "https://www.planalto.gov.br/ccivil_03/leis/l8078.htm",
                "name": "Lei 8.078/1990 (Código de Defesa do Consumidor), texto original",
                "anchor_claim": "art. 18, §1º",
                "verified_at": "2026-09-01T00:00:00Z",
                "http_status": 200,
            },
        ],
    }
    pagina.update(sobrescritas)
    return pagina


def portfolio_minimo(intent: str, **sobrescritas) -> dict:
    registro = {
        "intent_id": intent,
        "page_type": "verbete",
        "practice_area": "consumidor",
        "lane": "informativa",
        "family": "consumidor-garantia",
        "long_tail_query": "prazo de garantia legal de produto duravel",
        "working_title": "Garantia legal de produto duravel",
        "reader_problem": "comprou um produto que apresentou defeito e nao sabe ate quando pode reclamar",
        "distinct_because": "trata do prazo de reclamacao, nao da troca imediata",
    }
    registro.update(sobrescritas)
    return registro


def escreve_jsonl(caminho: pathlib.Path, registros: list[dict]) -> None:
    with open(caminho, "w", encoding="utf-8") as handle:
        for registro in registros:
            handle.write(json.dumps(registro, ensure_ascii=False) + "\n")


def roda_oraculo(paginas: list[dict], portfolio: list[dict],
                 oraculo: pathlib.Path = ORACULO,
                 exigir: str = "ambos") -> tuple[int, list[dict], str]:
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        arquivo_pagina = base / "candidato.jsonl"
        arquivo_portfolio = base / "portfolio.jsonl"
        escreve_jsonl(arquivo_pagina, paginas)
        escreve_jsonl(arquivo_portfolio, portfolio)
        processo = subprocess.run(
            [sys.executable, str(oraculo),
             "--pagina", str(arquivo_pagina),
             "--portfolio", str(arquivo_portfolio),
             "--exigir", exigir, "--json"],
            cwd=str(RAIZ), capture_output=True, text=True, check=False)
        vereditos = [json.loads(linha) for linha in processo.stdout.splitlines()
                     if linha.strip().startswith("{")]
        return processo.returncode, vereditos, processo.stdout + processo.stderr


class MotivoIdenticoAoDoIngest(unittest.TestCase):

    def test_lane_desconhecida_devolve_o_motivo_literal_do_v2ingest(self):
        intent = "oraculo-teste-lane-desconhecida"
        codigo, vereditos, saida = roda_oraculo(
            [pagina_minima(intent, lane="lane_que_nao_existe")],
            [portfolio_minimo(intent, lane="lane_que_nao_existe")])
        self.assertEqual(len(vereditos), 1, saida)
        motivos = vereditos[0]["ingest_reasons"]
        self.assertIn("lane_invalid:lane_que_nao_existe", motivos, saida)
        self.assertIn("portfolio_lane_invalid:lane_que_nao_existe", motivos, saida)
        self.assertFalse(vereditos[0]["entra_no_estoque"])
        self.assertEqual(codigo, 1, saida)

    def test_campo_ausente_reprova_nos_dois_eixos_com_o_nome_de_cada_um(self):
        intent = "oraculo-teste-sem-titulo"
        codigo, vereditos, saida = roda_oraculo(
            [pagina_minima(intent, title="")], [portfolio_minimo(intent)])
        self.assertEqual(len(vereditos), 1, saida)
        veredito = vereditos[0]
        # Eixo estoque: o vocabulário é o do v2ingest.
        self.assertIn("missing_required_field:title", veredito["ingest_reasons"], saida)
        # Eixo publicação: o vocabulário é o do censo, e é OUTRO de propósito.
        self.assertIn("falta_title", veredito["censo_criticos"], saida)
        self.assertFalse(veredito["publica"])
        self.assertEqual(codigo, 1, saida)

    def test_pagina_sem_defeito_passa_nos_dois_eixos(self):
        """Falso positivo: página boa não pode ser recusada por nenhum eixo."""
        intent = "oraculo-teste-pagina-limpa"
        codigo, vereditos, saida = roda_oraculo(
            [pagina_minima(intent)], [portfolio_minimo(intent)])
        self.assertEqual(len(vereditos), 1, saida)
        self.assertEqual(vereditos[0]["ingest_reasons"], [], saida)
        self.assertTrue(vereditos[0]["publica"], saida)
        self.assertTrue(vereditos[0]["entra_no_estoque"], saida)
        self.assertEqual(codigo, 0, saida)


class DecisorQueNaoRodaNuncaEVerde(unittest.TestCase):

    def test_relatorio_ausente_interrompe_em_vez_de_aprovar(self):
        modulo = carrega_oraculo(ORACULO)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as capturado:
                modulo.roda_eixo_estoque(pathlib.Path(tmp))
            self.assertIn("relatorio", str(capturado.exception))

    def test_censo_ausente_interrompe_em_vez_de_aprovar(self):
        modulo = carrega_oraculo(ORACULO)
        with tempfile.TemporaryDirectory() as tmp:
            base = pathlib.Path(tmp)
            (base / "tools").mkdir()
            (base / "tools" / modulo.CENSO_FONTE.name).write_text(
                "import sys\nsys.exit(3)\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as capturado:
                modulo.roda_eixo_publicacao(base)
            self.assertIn("veredito", str(capturado.exception))

    def test_mutante_que_engole_a_falha_do_ingest_morre(self):
        """Mutante: relatório ausente vira dicionário vazio (= nenhuma recusa)."""
        fonte = ORACULO.read_text(encoding="utf-8")
        alvo = """    if not relatorio.exists():
        raise SystemExit("""
        self.assertIn(alvo, fonte, "o trecho mutado nao existe mais no oraculo")
        with tempfile.TemporaryDirectory() as tmp:
            mutante = pathlib.Path(tmp) / "oraculo-mutante"
            mutante.write_text(fonte.replace(alvo, """    if not relatorio.exists():
        return {}
    if False:
        raise SystemExit("""), encoding="utf-8")
            modulo = carrega_oraculo(mutante)
            with tempfile.TemporaryDirectory() as vazio:
                # Com o mutante, o eixo estoque devolve {} em silêncio: nenhuma
                # recusa, nenhum erro. É o falso-verde que o teste acima mata.
                self.assertEqual(modulo.roda_eixo_estoque(pathlib.Path(vazio)), {})


class OraculoNaoTemReguaPropria(unittest.TestCase):

    def test_o_eixo_estoque_chama_o_binario_que_importa_v2ingest(self):
        modulo = carrega_oraculo(ORACULO)
        self.assertEqual(modulo.INGEST_CMD, "./cmd/ingest-v2-pages")
        fonte = (RAIZ / "cmd" / "ingest-v2-pages" / "main.go").read_text(encoding="utf-8")
        self.assertIn("v2ingest.Run", fonte,
                      "o comando do oraculo deixou de chamar o validador real")

    def test_o_eixo_publicacao_usa_o_censo_com_sha256_conferido(self):
        modulo = carrega_oraculo(ORACULO)
        self.assertEqual(modulo.CENSO_FONTE,
                         RAIZ / "tools" / "generate-v2-publication-severity")
        fonte = ORACULO.read_text(encoding="utf-8")
        self.assertIn("if sha256(destino_censo) != sha256(CENSO_FONTE):", fonte)

    def test_nada_e_copiado_por_link(self):
        """Ensaio é por CÓPIA: symlink/hardlink escreveria no acervo real."""
        fonte = ORACULO.read_text(encoding="utf-8")
        self.assertNotIn("os.symlink", fonte)
        self.assertNotIn("os.link", fonte)
        self.assertIn("shutil.copy2", fonte)

    def test_a_lista_do_que_ele_nao_cobre_aponta_ferramenta_que_existe(self):
        """Cobertura que cita comando inexistente manda o produtor ao vazio."""
        modulo = carrega_oraculo(ORACULO)
        self.assertTrue(modulo.FORA_DA_COBERTURA, "a lista nao pode ser vazia")
        for o_que, quem in modulo.FORA_DA_COBERTURA:
            self.assertTrue(o_que.strip())
            for termo in quem.split():
                # removeprefix, nunca lstrip: lstrip("./") come o ponto de
                # `.githooks/` e procura um diretorio que nao existe. O proprio
                # teste caiu nessa armadilha antes de ser corrigido.
                relativo = termo.removeprefix("./")
                if relativo.startswith(("tools/", ".githooks/", "cmd/", "data/")):
                    alvo = RAIZ / relativo
                    self.assertTrue(alvo.exists(), f"{quem}: {alvo} nao existe")

    def test_os_motivos_de_lote_declarados_existem_no_validador(self):
        """Lista de 'nao avaliado' que mente é pior que lista ausente."""
        modulo = carrega_oraculo(ORACULO)
        validador = (RAIZ / "internal" / "v2ingest" / "validate.go").read_text(encoding="utf-8")
        for motivo in modulo.MOTIVOS_DE_LOTE_ESTOQUE:
            self.assertIn(motivo, validador,
                          f"{motivo} nao existe mais em validate.go")


if __name__ == "__main__":
    unittest.main(verbosity=2)
