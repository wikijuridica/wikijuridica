#!/usr/bin/env python3
"""Prova por MUTAÇÃO a guarda que deixa a gêmea Markdown ser reentregue ao
IndexNow — e, sobretudo, prova que ela continua estreita.

POR QUE ESTA GUARDA EXISTE, com o número que a originou.

Medido em 2026-09-10: o relatório do Bing Webmaster mantinha DEZ URLs marcadas
como 5xx. As nove identificadas no log de origem são todas gêmeas
`/x/index.md`, e todas tomaram 503 em 2026-09-02, dentro da janela de ~16 h em
que o socket do systemd estava em migração (`portal_health.jsonl`: ok=false de
2026-09-01T21:37:39Z a 2026-09-02T14:00:01Z). As nove respondem 200 hoje,
conferidas uma a uma na borda. Quem retém o erro é o índice do Bing, e o único
canal para dizer a ele que a URL voltou é reentregar por IndexNow.

`generate-indexnow-direct-submit` recusava a lista inteira porque a gêmea não
está no sitemap — e ela não está lá por decisão de SEO, não por não existir
(CLAUDE.md §7: o canal de máquina tem caminho próprio para não dividir chave de
cache). A guarda passou a aceitar a gêmea por DERIVAÇÃO da rota-mãe.

O RISCO que este teste vigia é o do afrouxamento silencioso: se alguém trocar a
derivação por "aceita qualquer coisa que termine em .md", ou por comparação de
prefixo frouxa, volta a valer o defeito que a guarda existe para impedir —
submeter endereço que o portal não publica.

────────────────────────────────────────────────────────────────────────────
O QUE MUDOU EM 2026-09-16, e por que o texto acima FICA.

O diagnóstico de 2026-09-10 estava certo e o REMÉDIO era largo demais. Aceitar
a gêmea virou o padrão de uma lista que a traz SEMPRE: `deploy-publico:1506`
monta o payload do IndexNow reusando verbatim o `--purge-targets`, que emite
duas linhas por rota porque `/x/` e `/x/index.md` são duas CHAVES DE CACHE
(`generate-page-content-revision:738-741`). Correto para purgar; erro de
categoria para anunciar.

Medido na origem (`data/ops/indexnow_url_state.jsonl`, uma linha por URL por
lote realmente POSTado):

  - 2.422 de 13.941 eventos desde 2026-09-04 eram `.md` — 17,4%, em 1.968 URLs
    distintas, TODAS com HTTP 200;
  - no lote de 2026-09-16T15:50:19: 254 URLs = 127 HTML + 127 gêmeas, com as
    127 mães no mesmo lote. Exatamente 50% de duplicata;
  - antes do commit 224fb9ba (2026-09-10) o número era ZERO por construção.

E a gêmea diz de si mesma o que a decide: medido na borda em 2026-09-16,
`/sumulas/stj-409/index.md` responde 200 com
`link: <https://wikijuridica.com.br/sumulas/stj-409/>; rel="canonical"`.
Anunciá-la é pedir indexação de um endereço que se autodeclara duplicata.

Então a decisão saiu do reconhecedor e foi para `particiona_pedidas`: a gêmea é
DERIVÁVEL (o reconhecedor continua igual, e os testes dele continuam valendo) e
NÃO é anunciada por padrão. `--incluir-gemea-markdown` preserva a reentrega de
2026-09-10 como ato deliberado.

O CONTROLE QUE NÃO PODE CAIR, em nenhum dos dois modos: endereço que o portal
não publica continua REPROVANDO a execução inteira. Derivar nunca vira inventar.
"""
import importlib.machinery
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ, "tools", "generate-indexnow-direct-submit")

SITEMAP = {
    "https://wikijuridica.com.br/tributario/execfiscal-bem-de-familia/",
    "https://wikijuridica.com.br/trabalhista/salario-por-fora/",
    "https://wikijuridica.com.br/",
}


class GemeaMarkdown(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "gen_indexnow_direct_submit", FERRAMENTA).load_module()

    def aceita(self, url):
        return self.mod.e_gemea_de_rota_conhecida(url, SITEMAP)

    def test_gemea_de_rota_do_sitemap_e_aceita(self):
        # O caso REAL: nove destas foram recusadas em 2026-09-10.
        self.assertTrue(self.aceita(
            "https://wikijuridica.com.br/tributario/execfiscal-bem-de-familia/index.md"))
        self.assertTrue(self.aceita(
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/index.md"))

    def test_gemea_de_rota_que_o_sitemap_NAO_anuncia_e_recusada(self):
        # Esta é a razão de ser da guarda: derivar não pode virar inventar.
        self.assertFalse(self.aceita(
            "https://wikijuridica.com.br/inventada/nunca-publicada/index.md"))

    def test_dominio_alheio_com_caminho_igual_e_recusado(self):
        self.assertFalse(self.aceita(
            "https://exemplo.invalido/trabalhista/salario-por-fora/index.md"))

    def test_sufixo_parecido_nao_passa(self):
        for url in (
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/index.md.txt",
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/outro.md",
            "https://wikijuridica.com.br/trabalhista/salario-por-forA/index.md",
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/INDEX.MD",
        ):
            with self.subTest(url=url):
                self.assertFalse(self.aceita(url))

    def test_url_do_sitemap_nao_depende_desta_guarda(self):
        # A rota canônica entra pelo caminho normal; a guarda só trata a gêmea.
        self.assertFalse(self.aceita(
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/"))

    def test_a_gemea_da_home_segue_a_mesma_regra(self):
        self.assertTrue(self.aceita("https://wikijuridica.com.br/index.md"))


class ParticionaPedidas(unittest.TestCase):
    """A decisão de ANUNCIAR, que é outra coisa que a de DERIVAR.

    Estes testes são de COMPORTAMENTO, de propósito. O teste de fiação que
    existia aqui até 2026-09-16 conferia a presença de uma string no fonte
    (`and not e_gemea_de_rota_conhecida(u, conhecidas)`) — e uma asserção
    dessas casa com o texto e não com o efeito: ela seguiria verde se a lista
    filtrada fosse jogada fora na linha seguinte, e ficou vermelha por uma
    correção que melhorou o comportamento. Régua de fonte mede o fonte.
    """

    @classmethod
    def setUpClass(cls):
        cls.mod = importlib.machinery.SourceFileLoader(
            "gen_indexnow_direct_submit", FERRAMENTA).load_module()

    # A lista como `--purge-targets` a entrega: cada rota seguida da sua gêmea.
    # É a forma REAL medida no lote de 2026-09-16T15:50:19.
    PURGE_TARGETS = [
        "https://wikijuridica.com.br/",
        "https://wikijuridica.com.br/index.md",
        "https://wikijuridica.com.br/trabalhista/salario-por-fora/",
        "https://wikijuridica.com.br/trabalhista/salario-por-fora/index.md",
    ]

    def test_gemea_NAO_e_anunciada_por_padrao(self):
        anunciar, gemeas, fora = self.mod.particiona_pedidas(
            self.PURGE_TARGETS, SITEMAP)
        self.assertEqual(fora, [])
        self.assertEqual(len(gemeas), 2)
        self.assertEqual(anunciar, [
            "https://wikijuridica.com.br/",
            "https://wikijuridica.com.br/trabalhista/salario-por-fora/",
        ])
        # O que o defeito de 2026-09-10 fazia, dito como asserção:
        self.assertFalse([u for u in anunciar if u.endswith(".md")],
                         "nenhuma .md pode sair no anuncio padrao")

    def test_a_mae_nunca_se_perde_junto_com_a_gemea(self):
        # O controle pareado do descarte: filtrar duplicata não pode virar
        # "deixei de anunciar a página". Toda mãe da lista continua anunciada.
        anunciar, _, _ = self.mod.particiona_pedidas(self.PURGE_TARGETS, SITEMAP)
        for url in self.PURGE_TARGETS:
            if not url.endswith(".md"):
                self.assertIn(url, anunciar)

    def test_flag_explicita_reentrega_a_gemea_na_ordem_original(self):
        anunciar, gemeas, fora = self.mod.particiona_pedidas(
            self.PURGE_TARGETS, SITEMAP, incluir_gemea=True)
        self.assertEqual(fora, [])
        self.assertEqual(gemeas, [])
        self.assertEqual(anunciar, self.PURGE_TARGETS)

    def test_endereco_inventado_REPROVA_nos_dois_modos(self):
        # O controle que não cai: derivar nunca vira inventar. Se este teste
        # ficar verde com a URL ausente de `fora`, o comando passou a submeter
        # endereço que o portal não publica.
        inventada = "https://wikijuridica.com.br/inventada/nunca-publicada/index.md"
        alheia = "https://exemplo.invalido/trabalhista/salario-por-fora/index.md"
        for incluir in (False, True):
            with self.subTest(incluir_gemea=incluir):
                _, _, fora = self.mod.particiona_pedidas(
                    self.PURGE_TARGETS + [inventada, alheia], SITEMAP,
                    incluir_gemea=incluir)
                self.assertIn(inventada, fora)
                self.assertIn(alheia, fora)

    def test_lista_so_de_gemeas_nao_vira_anuncio_vazio_silencioso(self):
        anunciar, gemeas, fora = self.mod.particiona_pedidas(
            ["https://wikijuridica.com.br/index.md"], SITEMAP)
        self.assertEqual(anunciar, [])
        self.assertEqual(len(gemeas), 1)
        self.assertEqual(fora, [])

    def test_a_particao_esta_ligada_em_main(self):
        # Mutação de FIAÇÃO, e ela precisa compilar para valer: mutar só a
        # chamada deixaria `anunciar` declarado e não usado. O que se afirma
        # aqui é que main() consome o resultado da partição — a variável que
        # vai ao POST é a que saiu dela, e o contador de descarte vai à
        # evidência.
        fonte = open(FERRAMENTA, encoding="utf-8").read()
        self.assertIn("anunciar, gemeas, fora = particiona_pedidas(", fonte)
        self.assertIn("urls = anunciar", fonte)
        self.assertIn('"dropped_markdown_twins": gemeas_descartadas', fonte)


if __name__ == "__main__":
    unittest.main()
