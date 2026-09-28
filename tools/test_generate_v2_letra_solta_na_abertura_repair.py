#!/usr/bin/env python3
"""Prova por MUTAÇÃO o gerador datado que tira a letra solta da fonte da prosa
que o portal assina (`tools/generate-v2-letra-solta-na-abertura-repair-20260916`).

O QUE UM GERADOR DATADO TEM DE PROVAR, e o que cada teste aqui cobre:

  1. que ele troca SÓ o que declara — as outras 29 linhas de cada shard saem
     byte a byte, e a linha alvo sai com o sha256 que o plano prometeu;
  2. que ele é IDEMPOTENTE — a segunda passada não toca nada e não erra;
  3. que o CAS por LINHA aborta quando outra frente escreveu por cima;
  4. que o CAS por TRECHO carrega peso próprio, e não é enfeite ao lado do CAS
     por linha;
  5. que a invariância do `word_count` é conferida — reparo que muda a contagem
     do corpo faria o ingest rejeitar com `declared_word_count_incoherent` e a
     página sumiria do estoque sem ninguém ter pedido.

CADA GUARDA É PROVADA PELO MUTANTE QUE A DESLIGA: o teste mostra que, com a
guarda fora, o mesmo cenário passa e ESCREVE. Mutante que não roda não conta, e
por isso os mutantes aqui são o gerador REAL com uma troca textual, executado de
verdade contra uma raiz temporária — nunca uma reimplementação.

E cada cenário de defeito vem com o CONTROLE: a mesma passada sobre o estoque
limpo (a linha já reparada) sai com zero tocados e exit 0.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GERADOR = RAIZ / "tools/generate-v2-letra-solta-na-abertura-repair-20260916"
EPOCA = RAIZ / "tools/v2_stock_epoch.py"

SHARD = "data/editorial/v2_pages/stj-acordao-derivado-01.jsonl"
PORTFOLIO = "data/editorial/portfolio_v2/jurisprudencia-stj-acordao-derivada-01.jsonl"
INTENT = "jur-stj-resp-2218914"
ANTIGO = "jdireito civil e do consumidor"
NOVO = "direito civil e do consumidor"


def sha(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# O REGISTRO ANTERIOR, PRESERVADO PELO PRÓPRIO GERADOR, é o fixture da linha
# alvo. O porquê está no docstring de BaseDoReparo.
PRESERVADOS = RAIZ / ".agents/runtime/letra-solta-na-abertura-20260916/2026-09-16"


class BaseDoReparo(unittest.TestCase):
    """Monta uma raiz temporária com o estoque no estado ANTERIOR ao reparo.

    ★ POR QUE O FIXTURE NÃO É O SHARD VIVO
    
    Foi tentado, e quebrou na hora em que o reparo rodou de verdade: o teste
    copiava `data/editorial/v2_pages/...` e, depois do `--aplicar`, passou a
    copiar o estoque JÁ CORRIGIDO — 7 de 12 casos viraram "já reparado" e
    deixaram de medir o reparo. Teste cujo fixture é o alvo do trabalho mede a
    si mesmo depois da primeira execução.

    O fixture da LINHA ALVO é o registro anterior que o gerador preservou em
    `.agents/runtime/` (a regra de v2_pages exige essa preservação), e ele é
    CONFERIDO contra `linha_sha256_antes` do plano: fixture que não bate com o
    que o plano viu reprova aqui, em vez de medir outra coisa em silêncio.

    As outras linhas do shard vêm do disco vivo — são as irmãs REAIS, e é
    contra elas que se prova "não toquei em mais nada".

    A raiz é temporária: o lease de época deriva o offset do lock do caminho da
    raiz (v2_stock_epoch:82), então ela não disputa o lock da raiz viva.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="letra-solta-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "tools").mkdir()
        shutil.copy2(GERADOR, self.tmp / "tools" / GERADOR.name)
        shutil.copy2(EPOCA, self.tmp / "tools" / EPOCA.name)
        self.gerador = self.tmp / "tools" / GERADOR.name

        planos = {alvo["arquivo"]: alvo for alvo in self.plano()}
        for relativo in (SHARD, PORTFOLIO):
            alvo = planos[relativo]
            preservado = PRESERVADOS / (Path(relativo).stem + "." + INTENT + ".jsonl")
            if not preservado.exists():
                self.fail(f"o registro anterior de {relativo} não está preservado em {preservado}: "
                          "sem ele não há como montar o estado pré-reparo sem inventá-lo")
            linha_antiga = preservado.read_text(encoding="utf-8").rstrip("\n")
            if sha(linha_antiga) != alvo["linha_sha256_antes"]:
                self.fail(f"o registro preservado de {relativo} não é o que o plano viu "
                          f"({sha(linha_antiga)} != {alvo['linha_sha256_antes']})")

            vivas = (RAIZ / relativo).read_text(encoding="utf-8")[:-1].split("\n")
            agulha = '"intent_id":"' + INTENT + '"'
            linhas = [linha_antiga if agulha in linha else linha for linha in vivas]
            if linha_antiga not in linhas:
                self.fail(f"{relativo} não tem mais a linha de {INTENT}: o alvo do reparo sumiu do estoque")
            if len(linhas) < 10:
                self.fail(f"{relativo} tem {len(linhas)} linha(s): o controle de 'não toquei nas outras' "
                          "precisa de irmãs de verdade para significar alguma coisa")
            destino = self.tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    # -- utilidades ---------------------------------------------------------
    def roda(self, *args, gerador=None):
        proc = subprocess.run(
            [sys.executable, str(gerador or self.gerador), *args],
            capture_output=True, text=True, cwd=str(self.tmp))
        return proc.returncode, proc.stdout + proc.stderr

    def linhas(self, relativo):
        return (self.tmp / relativo).read_text(encoding="utf-8")[:-1].split("\n")

    def linha_alvo(self, relativo):
        alvo = '"intent_id":"' + INTENT + '"'
        for indice, linha in enumerate(self.linhas(relativo)):
            if alvo in linha:
                return indice, linha
        self.fail(f"{INTENT} não está em {relativo}")

    def mutante(self, *trocas):
        """O gerador REAL com uma troca textual — nunca uma reimplementação."""
        fonte = self.gerador.read_text(encoding="utf-8")
        for de, para in trocas:
            self.assertIn(de, fonte, f"âncora do mutante não casou: {de!r}")
            fonte = fonte.replace(de, para)
        caminho = self.tmp / "tools" / "mutante-do-reparo"
        caminho.write_text(fonte, encoding="utf-8")
        return caminho

    def plano(self):
        """Le ALVOS do gerador real, sem copiar a tabela para o teste.

        Copiar os hashes aqui criaria uma segunda fonte de verdade que
        envelhece sozinha -- e o teste passaria a medir a copia.
        """
        import importlib.machinery
        import importlib.util
        carregador = importlib.machinery.SourceFileLoader("reparo_letra_solta", str(self.gerador))
        spec = importlib.util.spec_from_loader(carregador.name, carregador)
        modulo = importlib.util.module_from_spec(spec)
        carregador.exec_module(modulo)
        return modulo.ALVOS

    def perturba(self, relativo, indice, de, para):
        linhas = self.linhas(relativo)
        self.assertIn(de, linhas[indice])
        linhas[indice] = linhas[indice].replace(de, para, 1)
        (self.tmp / relativo).write_text("\n".join(linhas) + "\n", encoding="utf-8")


class TestReparaSoOQueDeclara(BaseDoReparo):

    def test_troca_a_linha_alvo_e_preserva_as_outras(self):
        antes_shard = self.linhas(SHARD)
        antes_portfolio = self.linhas(PORTFOLIO)
        indice_shard, linha_antes = self.linha_alvo(SHARD)

        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)

        depois_shard = self.linhas(SHARD)
        depois_portfolio = self.linhas(PORTFOLIO)
        self.assertEqual(len(antes_shard), len(depois_shard))
        self.assertEqual(len(antes_portfolio), len(depois_portfolio))

        # O CONTROLE QUE IMPORTA: todas as irmãs byte a byte, nos dois shards.
        # O número não é chumbado — ele é AFIRMADO: N de M, com piso, para que
        # um shard que encolhesse não deixasse o controle passar com 1 linha.
        intocadas = 0
        for i, (a, b) in enumerate(zip(antes_shard, depois_shard)):
            if i == indice_shard:
                continue
            self.assertEqual(a, b, f"linha {i + 1} do shard mudou sem ser alvo")
            intocadas += 1
        self.assertEqual(intocadas, len(antes_shard) - 1,
                         "toda linha que não é o alvo tem de sair byte a byte")
        self.assertGreaterEqual(intocadas, 10,
                                f"só {intocadas} irmã(s) no shard: o controle não significa nada")

        indice_portfolio, _ = self.linha_alvo(PORTFOLIO)
        for i, (a, b) in enumerate(zip(antes_portfolio, depois_portfolio)):
            if i == indice_portfolio:
                continue
            self.assertEqual(a, b, f"linha {i + 1} do portfólio mudou sem ser alvo")

        # A linha alvo é a antiga menos a letra solta, e nada além disso.
        self.assertEqual(depois_shard[indice_shard], linha_antes.replace(ANTIGO, NOVO))
        self.assertNotIn(ANTIGO, depois_shard[indice_shard])
        self.assertEqual(depois_shard[indice_shard].count(NOVO), 7)
        self.assertNotIn(ANTIGO, "\n".join(depois_portfolio))

        # E o CAS de chegada: a linha reparada tem de ter o sha256 que o plano
        # do gerador prometeu. Sem isto o teste aceitaria QUALQUER troca que
        # tirasse a letra solta, inclusive uma que mexesse em outro campo.
        planos = {alvo["arquivo"]: alvo for alvo in self.plano()}
        self.assertEqual(sha(depois_shard[indice_shard]),
                         planos[SHARD]["linha_sha256_depois"])
        self.assertEqual(sha(depois_portfolio[indice_portfolio]),
                         planos[PORTFOLIO]["linha_sha256_depois"])

    def test_o_registro_anterior_fica_guardado_antes_da_escrita(self):
        _, linha_antes = self.linha_alvo(SHARD)
        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)
        guardados = list((self.tmp / ".agents/runtime/letra-solta-na-abertura-20260916/2026-09-16").glob("*.jsonl"))
        self.assertEqual(len(guardados), 2, f"esperava o registro anterior dos dois alvos: {guardados}")
        conteudos = [c.read_text(encoding="utf-8") for c in guardados]
        self.assertIn(linha_antes + "\n", conteudos,
                      "o registro anterior guardado não é a linha que estava no disco")

    def test_word_count_declarado_continua_batendo_com_o_corpo(self):
        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)
        self.assertIn("word_count: declarado=1355 corpo=1355", saida)
        _, linha = self.linha_alvo(SHARD)
        self.assertEqual(json.loads(linha)["word_count"], 1355)


class TestIdempotencia(BaseDoReparo):

    def test_segunda_passada_nao_toca_nada(self):
        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)
        depois_da_primeira = (self.tmp / SHARD).read_bytes()

        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)
        self.assertIn("reparados agora: 0", saida)
        self.assertIn("já reparados: 2", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), depois_da_primeira,
                         "a segunda passada reescreveu o shard")

    def test_controle_estoque_limpo_sai_zero(self):
        """O MESMO CENÁRIO SEM O DEFEITO: nada a fazer, exit 0, disco intacto."""
        for relativo in (SHARD, PORTFOLIO):
            texto = (self.tmp / relativo).read_text(encoding="utf-8")
            (self.tmp / relativo).write_text(texto.replace(ANTIGO, NOVO), encoding="utf-8")
        limpo = (self.tmp / SHARD).read_bytes()
        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 0, saida)
        self.assertIn("reparados agora: 0", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), limpo)


class TestCASPorLinha(BaseDoReparo):
    """Outra frente escreveu na MESMA linha: o reparo aborta e não escreve."""

    DE = '"h1":"Recurso Especial 2.218.914'
    PARA = '"h1":"Recurso especial 2.218.914'

    def test_cas_falha_e_o_disco_fica_intacto(self):
        indice, _ = self.linha_alvo(SHARD)
        self.perturba(SHARD, indice, self.DE, self.PARA)
        perturbado = (self.tmp / SHARD).read_bytes()

        rc, saida = self.roda("--aplicar")
        self.assertEqual(rc, 2, saida)
        self.assertIn("CAS FALHOU", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), perturbado,
                         "o CAS reprovou e o gerador escreveu assim mesmo")

    def test_MUTANTE_sem_o_cas_de_linha_o_mesmo_cenario_escreve(self):
        indice, _ = self.linha_alvo(SHARD)
        self.perturba(SHARD, indice, self.DE, self.PARA)
        perturbado = (self.tmp / SHARD).read_bytes()

        # Desliga SÓ o CAS por linha. O CAS por sha256 final também precisa sair,
        # senão é ele quem pega — e o que se quer provar é o peso do primeiro.
        mutante = self.mutante(
            ('if atual != alvo["linha_sha256_antes"]:', 'if False:'),
            ('if sha256_de(nova_linha) != alvo["linha_sha256_depois"]:', 'if False:'),
        )
        rc, saida = self.roda("--aplicar", gerador=mutante)
        self.assertEqual(rc, 0, saida)
        self.assertNotEqual((self.tmp / SHARD).read_bytes(), perturbado,
                            "o mutante sem CAS não escreveu: o teste acima não prova a guarda")


class TestCASPorTrecho(BaseDoReparo):
    """Uma das 7 ocorrências já foi consertada à mão: a contagem não bate mais.

    Sozinho, o CAS por linha já pegaria isso (o sha muda). O que este teste
    mede é se o CAS por TRECHO carrega peso PRÓPRIO — se ele some, a única
    coisa entre o estoque e uma troca cega é um hash que alguém pode
    recalcular.
    """

    def cenario(self):
        indice, linha = self.linha_alvo(SHARD)
        linhas = self.linhas(SHARD)
        linhas[indice] = linha.replace(ANTIGO, NOVO, 1)  # 7 -> 6 ocorrências
        (self.tmp / SHARD).write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return (self.tmp / SHARD).read_bytes()

    def test_com_o_cas_de_linha_desligado_o_trecho_ainda_aborta(self):
        antes = self.cenario()
        mutante = self.mutante(('if atual != alvo["linha_sha256_antes"]:', 'if False:'))
        rc, saida = self.roda("--aplicar", gerador=mutante)
        self.assertEqual(rc, 2, saida)
        self.assertIn("CAS DO TRECHO FALHOU", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), antes)

    def test_MUTANTE_sem_o_cas_de_trecho_o_mesmo_cenario_escreve(self):
        antes = self.cenario()
        mutante = self.mutante(
            ('if atual != alvo["linha_sha256_antes"]:', 'if False:'),
            ('if ocorrencias != alvo["ocorrencias"]:', 'if False:'),
            ('if sha256_de(nova_linha) != alvo["linha_sha256_depois"]:', 'if False:'),
        )
        rc, saida = self.roda("--aplicar", gerador=mutante)
        self.assertEqual(rc, 0, saida)
        self.assertNotEqual((self.tmp / SHARD).read_bytes(), antes,
                            "o mutante sem o CAS de trecho não escreveu: o teste acima não prova a guarda")


class TestInvarianciaDoWordCount(BaseDoReparo):
    """Reparo que mexe na contagem do corpo é reparo errado.

    `jdireito` e `direito` são UM token cada pela fórmula canônica
    (`[0-9A-Za-zÀ-ÖØ-öø-ÿ]+`), então o corpo tem de contar igual. Um payload que
    acrescentasse palavra passaria no CAS de linha e deixaria `word_count`
    declarado divergente do corpo — e o ingest rejeitaria a página com
    `declared_word_count_incoherent`.
    """

    # O payload alternativo acrescenta UMA palavra ao corpo. O sha256 final
    # deixa de bater por construção, então o CAS final sai junto: o que se mede
    # aqui é a guarda de contagem, não a de hash.
    TROCAS = (
        ('TRECHO_NOVO = "direito civil e do consumidor"',
         'TRECHO_NOVO = "direito civil e do consumidor brasileiro"'),
        ('if sha256_de(nova_linha) != alvo["linha_sha256_depois"]:', 'if False:'),
    )

    def test_payload_que_muda_a_contagem_aborta(self):
        antes = (self.tmp / SHARD).read_bytes()
        mutante = self.mutante(*self.TROCAS)
        rc, saida = self.roda("--aplicar", gerador=mutante)
        self.assertEqual(rc, 2, saida)
        self.assertIn("o corpo mudou de", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), antes)

    def test_MUTANTE_sem_a_guarda_de_contagem_o_mesmo_payload_escreve(self):
        antes = (self.tmp / SHARD).read_bytes()
        mutante = self.mutante(*self.TROCAS,
                               ("if palavras_antes != palavras_depois:", "if False:"))
        rc, saida = self.roda("--aplicar", gerador=mutante)
        self.assertEqual(rc, 0, saida)
        self.assertNotEqual((self.tmp / SHARD).read_bytes(), antes)
        _, linha = self.linha_alvo(SHARD)
        registro = json.loads(linha)
        corpo = [registro["opening"]]
        for secao in registro["sections"]:
            corpo += [secao["heading"], secao["text"]]
        for item in registro["faq"]:
            corpo += [item["q"], item["a"]]
        contado = len(re.findall(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+", " ".join(corpo)))
        self.assertNotEqual(registro["word_count"], contado,
                            "o mutante devia ter deixado word_count incoerente com o corpo")


class TestDryRunNaoEscreve(BaseDoReparo):

    def test_sem_aplicar_o_disco_nao_muda(self):
        antes_shard = (self.tmp / SHARD).read_bytes()
        antes_portfolio = (self.tmp / PORTFOLIO).read_bytes()
        rc, saida = self.roda()
        self.assertEqual(rc, 0, saida)
        self.assertIn("dry-run", saida)
        self.assertEqual((self.tmp / SHARD).read_bytes(), antes_shard)
        self.assertEqual((self.tmp / PORTFOLIO).read_bytes(), antes_portfolio)
        self.assertFalse((self.tmp / ".agents/runtime/letra-solta-na-abertura-20260916").exists(),
                         "o dry-run guardou registro anterior: ele não escreve nada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
