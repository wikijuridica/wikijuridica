#!/usr/bin/env python3
"""Testes da guarda de apply-dynamic-redirect-rules.

O QUE ESTES TESTES IMPEDEM DE VOLTAR. A regra de barra final atinge TODA a
superfície pública. A versão que estava no repositório até 2026-09-04 não
excluía `.css` nem `.js`: aplicá-la mandaria `/assets/wj-<hash>.css` para 301 e
as 10.141 páginas ficariam sem estilo, com a `location` do nginx perfeitamente
correta e o sintoma apontando para o lugar errado.

O conserto não foi só editar a expressão — foi pôr uma guarda no caminho da
escrita, para que a próxima edição distraída da expressão não chegue à zona.
Estes testes provam que a guarda **recusa**, e não apenas que ela existe: guarda
que só foi vista aprovar nunca foi vista guardar.
"""
import importlib.machinery
import importlib.util
import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALVO = os.path.join(RAIZ, "tools", "apply-dynamic-redirect-rules")

_spec = importlib.util.spec_from_loader(
    "apply_dynamic_redirect_rules",
    importlib.machinery.SourceFileLoader("apply_dynamic_redirect_rules", ALVO),
)
apply = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(apply)

# Expressão sem a exclusão dos diretórios de asset: é exatamente o texto que
# estava versionado e que teria apagado o estilo do acervo inteiro.
EXPRESSAO_DEFEITUOSA = (
    'not ends_with(http.request.uri.path, "/") '
    'and not starts_with(http.request.uri.path, "/api") '
    'and not ends_with(http.request.uri.path, ".html")'
)


def regra(expressao, enabled=True):
    return {
        "action": "redirect",
        "enabled": enabled,
        "expression": expressao,
        "action_parameters": {
            "from_value": {"status_code": 301, "preserve_query_string": True}
        },
    }


class TestGuardaRecusa(unittest.TestCase):
    def _com_public(self, arquivos):
        """Roda a guarda contra um public/ fabricado."""
        gate = apply.carrega_gate()
        original = gate.PUBLICO
        tmp = tempfile.TemporaryDirectory()
        for caminho in arquivos:
            completo = os.path.join(tmp.name, caminho.lstrip("/"))
            os.makedirs(os.path.dirname(completo), exist_ok=True)
            with open(completo, "w", encoding="utf-8") as fh:
                fh.write("x")
        gate.PUBLICO = tmp.name

        # A guarda importa o gate de novo; fixa a instância já ajustada.
        original_carrega = apply.carrega_gate
        apply.carrega_gate = lambda: gate
        try:
            return apply.recusa_por_arquivo_quebrado
        finally:
            self.addCleanup(setattr, gate, "PUBLICO", original)
            self.addCleanup(setattr, apply, "carrega_gate", original_carrega)
            self.addCleanup(tmp.cleanup)

    def test_recusa_expressao_que_apaga_a_folha_de_estilo(self):
        guarda = self._com_public(["/assets/wj-abc.css"])
        motivos = guarda([regra(EXPRESSAO_DEFEITUOSA)])
        self.assertTrue(
            motivos,
            "a guarda aprovou a expressão que manda a folha de estilo para 301 — "
            "é exatamente o defeito que ela existe para impedir",
        )
        self.assertIn("wj-abc.css", motivos[0])

    def test_aprova_expressao_que_exclui_os_assets(self):
        guarda = self._com_public(["/assets/wj-abc.css"])
        segura = EXPRESSAO_DEFEITUOSA + ' and not starts_with(http.request.uri.path, "/assets/")'
        self.assertEqual(guarda([regra(segura)]), [])

    def test_regra_desligada_nao_e_avaliada(self):
        """Regra com enabled=false não redireciona ninguém."""
        guarda = self._com_public(["/assets/wj-abc.css"])
        self.assertEqual(guarda([regra(EXPRESSAO_DEFEITUOSA, enabled=False)]), [])

    def test_public_vazio_recusa_em_vez_de_aprovar(self):
        """Sem os arquivos servidos não há como afirmar que a regra é segura.
        Aprovar por ausência de evidência seria o pior modo de falha aqui."""
        guarda = self._com_public([])
        motivos = guarda([regra(EXPRESSAO_DEFEITUOSA)])
        self.assertTrue(motivos)
        self.assertIn("public/", motivos[0])


class TestRegraVersionadaEhAplicavel(unittest.TestCase):
    def test_a_regra_do_repositorio_passa_na_guarda(self):
        """Anti-regressão da expressão versionada: se alguém retirar a exclusão
        dos assets, este teste fica vermelho antes de a regra chegar à zona."""
        with open(apply.CANONICO, encoding="utf-8") as fh:
            regras = json.load(fh)["rules"]
        gate = apply.carrega_gate()
        if not gate.arquivos_servidos_pelo_nome():
            self.skipTest("public/ ausente nesta árvore")
        self.assertEqual(
            apply.recusa_por_arquivo_quebrado(regras),
            [],
            "a regra versionada quebraria arquivo servido e não pode ser aplicada",
        )

    def test_preserva_query_string(self):
        """Sem isto, o 301 descartaria utm_*/gclid e a medição de origem de
        tráfego morreria no redirect."""
        with open(apply.CANONICO, encoding="utf-8") as fh:
            regras = json.load(fh)["rules"]
        for r in regras:
            destino = r["action_parameters"]["from_value"]
            self.assertTrue(destino.get("preserve_query_string"))
            self.assertEqual(destino.get("status_code"), 301)


if __name__ == "__main__":
    sys.exit(0 if unittest.main(exit=False).result.wasSuccessful() else 1)
