#!/usr/bin/env python3
"""`--purge-targets` só LISTA rotas e nunca grava: o teto de churn não pode barrá-lo.

Medido em 2026-09-08, no deploy `--ressemear` que levou a url do LexML ao
JSON-LD de 4.259 rotas (42 % do acervo): o passo 6 do `deploy-publico` chamou
`generate-page-content-revision --purge-targets`, o teto de churn (5 %) devolveu
"RECUSADO" com exit 1, o deploy leu isso como "registro de revisao indisponivel"
e purgou a borda inteira — depois de a publicação já ter purgado as 4.058
páginas reescritas por tag. O aquecimento anterior foi jogado fora e o
diagnóstico impresso era falso.

O teste roda o gerador de verdade (subprocesso, sem dublê) sobre um acervo
sintético em diretório temporário, com os caminhos do módulo redirecionados por
um `sitecustomize`-like: 20 rotas no ledger, 10 com texto novo (50 % > teto).
Sem `--purge-targets`, o teto barra (exit 1, "RECUSADO"). Com `--purge-targets`,
o gerador lista as 10 rotas mudadas, sai 0 e NÃO toca no ledger.
"""
from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = RAIZ / "tools" / "generate-page-content-revision"


def carrega_modulo():
    # O arquivo nao tem extensao .py: sem o loader explicito o spec sai None.
    loader = importlib.machinery.SourceFileLoader("gpcr", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader("gpcr", loader)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TetoDeChurnNaoBarraListagem(unittest.TestCase):
    def setUp(self) -> None:
        self.modulo = carrega_modulo()
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        self.modulo.PAGES_JSON = base / "pages.json"
        self.modulo.LEDGER = base / "ledger.jsonl"
        self.modulo.ASSINATURA_FORMULA = base / "formula.txt"
        self.modulo.PUBLIC = base / "public-inexistente"

        paginas = []
        ledger = []
        for i in range(20):
            caminho = f"/familia/rota-{i:02d}/"
            texto_antigo = {campo: f"{campo} antigo {i}" for campo in self.modulo.CAMPOS_DE_CONTEUDO}
            digest_antigo = hashlib.sha256(
                json.dumps(texto_antigo, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            ledger.append({"path": caminho, "content_sha256": digest_antigo,
                           "revised_on": "2026-08-01"})
            pagina = dict(texto_antigo)
            if i < 10:  # metade do acervo reescrita: 50 % > TETO_CHURN_FRACAO
                pagina["summary"] = f"summary novo {i}"
            pagina["path"] = caminho
            pagina["unique_intent_id"] = f"intent-{i}"
            paginas.append(pagina)
        self.modulo.PAGES_JSON.write_text(json.dumps(paginas), encoding="utf-8")
        self.modulo.LEDGER.write_text(
            "".join(json.dumps(l) + "\n" for l in ledger), encoding="utf-8")
        self.ledger_antes = self.modulo.LEDGER.read_bytes()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def roda(self, *argv: str) -> tuple[int, str]:
        saida = io.StringIO()
        sys.argv = ["generate-page-content-revision", *argv]
        with redirect_stdout(saida):
            codigo = self.modulo.main()
        return codigo, saida.getvalue()

    def test_sem_purge_targets_o_teto_barra(self) -> None:
        codigo, saida = self.roda("--dry-run")
        self.assertEqual(codigo, 1)
        self.assertIn("RECUSADO: o teto de churn", saida)
        # A redacao ganhou "ja publicadas" em 2026-09-16, quando o denominador
        # passou a ser a base publicada em vez do acervo inteiro. O NUMERO nao
        # mudou para este cenario (as 20 rotas ja estavam no ledger), e e' o
        # numero que este teste cobra.
        self.assertIn("10 de 20", saida)
        self.assertIn("50.0%", saida)
        self.assertIn("estreias no lote: 0", saida)

    def test_estreia_nao_conta_no_teto_de_churn(self) -> None:
        """★ O CASO MEDIDO EM PRODUCAO (2026-09-16)

        O deploy das 7.538 paginas de acordao publicou, purgou 60.782 URLs,
        aqueceu 37.570 objetos e anunciou 7.708 ao IndexNow -- e SO ENTAO
        recusou com `rotas que seriam re-datadas: 7708 de 18699 (41.2%)`.
        As 7.708 eram as paginas NOVAS.

        Rota que nasce hoje tem `lastmod` de hoje por definicao: ela e'
        anunciada pela PRIMEIRA vez, nao "reanuncia tudo ao crawler", que e' o
        dano que o teto existe para impedir. Contar estreia como churn faz a
        guarda reprovar exatamente o que a fabrica existe para produzir.

        PROVA POR MUTACAO: devolver `quantas_redatam` para `quantas_mudam` na
        fracao, ou o denominador para `len(atual)`, deixa este teste VERMELHO --
        e o teste acima continua verde, porque naquele cenario nao ha estreia.
        Os dois juntos separam as duas contas.
        """
        import hashlib
        import json as _json
        # Acervo: as 20 do setUp (nenhuma re-datada agora) MAIS 20 estreias.
        paginas = _json.loads(self.modulo.PAGES_JSON.read_text(encoding="utf-8"))
        ledger = []
        for i, pagina in enumerate(paginas):
            # Nenhuma muda: o content_sha256 do ledger bate com o da pagina.
            texto = {k: v for k, v in pagina.items()
                     if k not in ("path", "unique_intent_id")}
            digest = hashlib.sha256(
                _json.dumps(texto, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            ledger.append({"path": pagina["path"], "content_sha256": digest,
                           "revised_on": "2026-08-01"})
        for i in range(20):
            paginas.append({"path": f"/estreia-{i}/", "summary": f"estreia {i}",
                            "unique_intent_id": f"novo-{i}"})
        self.modulo.PAGES_JSON.write_text(_json.dumps(paginas), encoding="utf-8")
        self.modulo.LEDGER.write_text(
            "".join(_json.dumps(l) + "\n" for l in ledger), encoding="utf-8")

        codigo, saida = self.roda("--dry-run")
        # 20 estreias em 40 rotas = 50% do acervo, MAS 0 de 20 ja publicadas.
        self.assertNotIn("RECUSADO", saida)
        self.assertEqual(codigo, 0, saida)

    def test_purge_targets_lista_as_mudadas_e_nao_grava(self) -> None:
        codigo, saida = self.roda("--purge-targets")
        self.assertEqual(codigo, 0, saida)
        self.assertNotIn("RECUSADO", saida)
        linhas = [l for l in saida.splitlines() if l.strip()]
        rotas = sorted(l for l in linhas if not l.endswith("index.md"))
        gemeas = sorted(l for l in linhas if l.endswith("index.md"))
        self.assertEqual(rotas, [f"/familia/rota-{i:02d}/" for i in range(10)])
        self.assertEqual(gemeas, [f"/familia/rota-{i:02d}/index.md" for i in range(10)])
        self.assertEqual(self.modulo.LEDGER.read_bytes(), self.ledger_antes,
                         "--purge-targets gravou no ledger")


if __name__ == "__main__":
    unittest.main()
