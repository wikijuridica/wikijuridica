#!/usr/bin/env python3
"""A FIACAO do vigia: etapa escrita no runner tem de EXECUTAR em producao.

POR QUE ESTE TESTE EXISTE, com a medicao que o obriga (2026-09-16)
==================================================================
`tools/run-qualidade-diaria` tem duas reguas de escopo e elas se contradizem
para quem escreve uma etapa nova:

  `roda_longa NOME ...`        pula a etapa quando WIKI_QUALIDADE_ESCOPO=curto
  `if somente_longas; then`    quando ESCOPO=longo, roda uma LISTA FIXA e sai
                               com `exit 0` antes do resto do arquivo

As duas units instaladas sao `wikijuridica-qualidade-diaria` (curto) e
`wikijuridica-qualidade-longa` (longo). NENHUMA usa `tudo`. Logo, uma etapa
escrita com `roda_longa` FORA do bloco `somente_longas` nao roda em lugar
nenhum: no curto ela e' registrada como "pulada" e no longo o script ja' saiu.
Ela aparece no arquivo, aparece no `grep`, e mede zero — que e' a definicao de
detector orfao, um degrau acima.

Hoje as tres etapas em `roda_longa` (teste-lote-3, suite-completa,
sca-staticcheck) TEM a linha gemea dentro do bloco. Este teste congela isso:
quem escrever a quarta sem a gemea quebra aqui, e nao seis meses depois quando
alguem notar que a etapa nunca deixou linha no ledger.

E cobre a segunda armadilha da mesma familia, ja' catalogada em
`internal/redesocialcompletude/integracao_test.go`: etapa que aponta para
ferramenta inexistente ou sem bit de execucao. O `timeout ... "$@"` do `roda()`
falharia em runtime, de madrugada, com exit 126/127 — e o ledger guardaria
"vermelho" sem dizer que o defeito e' a fiacao, nao o produto.
"""
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIGIA = os.path.join(RAIZ, "tools", "run-qualidade-diaria")
# WIKI_UNITS_DIR existe para a PROVA POR MUTACAO deste arquivo, e nao para
# afrouxar nada: mutar a unit de producao para provar o teste significaria
# escrever em ops/systemd/ com o systemd vivo, e o custo de um restauro
# imperfeito seria a bancada diaria parar. Com a costura, o mutante monta uma
# arvore de units de mentira e o disco de producao nao e' tocado.
UNITS = os.environ.get("WIKI_UNITS_DIR") or os.path.join(RAIZ, "ops", "systemd")

# Globs de descoberta: sao as RAIZES de que tools/check-detector-orfao deriva o
# censo. Perder um aqui cega o censo la'.
GLOBS_ESPERADOS = ("tools/test_*.py", "tools/test_*.sh", "tools/*-selftest")


def fonte():
    with open(VIGIA, encoding="utf-8") as f:
        return f.read()


def linhas_uteis(texto):
    return [l for l in texto.split("\n") if not l.lstrip().startswith("#")]


def bloco_somente_longas(texto):
    """O trecho entre `if somente_longas; then` e o `fi` que o fecha."""
    linhas = texto.split("\n")
    inicio = next((i for i, l in enumerate(linhas) if l.startswith("if somente_longas; then")), None)
    if inicio is None:
        return None, linhas
    fim = next((i for i in range(inicio + 1, len(linhas)) if linhas[i] == "fi"), len(linhas))
    return linhas[inicio:fim], linhas[:inicio] + linhas[fim:]


NOME_DE_ETAPA = re.compile(r'^\s*(roda|roda_longa)\s+"?([A-Za-z0-9._:-]+)"?\s')


class TestFiacaoDoVigia(unittest.TestCase):
    def test_nenhuma_unit_usa_escopo_tudo(self):
        """A premissa do teste seguinte, MEDIDA e nao suposta."""
        escopos = []
        for nome in os.listdir(UNITS):
            if not nome.endswith(".service"):
                continue
            with open(os.path.join(UNITS, nome), encoding="utf-8", errors="ignore") as f:
                corpo = f.read()
            if "run-qualidade-diaria" not in corpo:
                continue
            for m in re.finditer(r"WIKI_QUALIDADE_ESCOPO=(\w+)", corpo):
                escopos.append((nome, m.group(1)))
        self.assertTrue(escopos, "nenhuma unit aciona o vigia — o ledger diario nasceria vazio")
        self.assertNotIn("tudo", [e for _, e in escopos],
                         f"se alguma unit passar a usar 'tudo', a regra de roda_longa muda: {escopos}")

    def test_toda_etapa_roda_longa_tem_gemea_no_bloco_longo(self):
        texto = fonte()
        bloco, fora = bloco_somente_longas(texto)
        self.assertIsNotNone(bloco, "o bloco `if somente_longas; then` sumiu do vigia")
        no_bloco = {m.group(2) for l in bloco for m in [NOME_DE_ETAPA.match(l)] if m}
        longas_fora = {m.group(2) for l in linhas_uteis("\n".join(fora))
                       for m in [NOME_DE_ETAPA.match(l)] if m and m.group(1) == "roda_longa"}
        # o helper do lote 3 nomeia a etapa por variavel; ele tem caso proprio
        longas_fora = {n for n in longas_fora if "$" not in n}
        orfas = sorted(n for n in longas_fora if n not in no_bloco)
        self.assertEqual(orfas, [], (
            "etapa(s) em roda_longa sem linha gemea dentro de `if somente_longas`: "
            f"{orfas}. No escopo curto elas sao PULADAS e no longo o script sai antes "
            "de chegar nelas — a etapa existe no arquivo e mede zero"))

    def test_toda_etapa_aponta_para_ferramenta_executavel(self):
        """O bit de execucao so' e' exigido de quem E' o comando.

        Medido ao escrever este teste: duas etapas invocam o alvo com
        interpretador explicito (`roda "test-edge-redirect-drift" 60 python3
        "$RAIZ/tools/test_check_edge_redirect_drift.py"`), e para elas o bit e'
        irrelevante — quem executa e' o `python3`. Exigir o bit ali seria um
        falso positivo do teste, e teste que acusa o que nao e' defeito ensina a
        equipe a ignora-lo. O que continua valendo para TODAS e' a existencia do
        arquivo.
        """
        alvo = re.compile(r'"\$RAIZ/(tools/[A-Za-z0-9._-]+)"')
        interpretador = re.compile(r'(python3|bash|sh|\$GO_MODERN|go-modern)\s+"\$RAIZ/(tools/[A-Za-z0-9._-]+)"')
        faltando, sem_bit = [], []
        for linha in linhas_uteis(fonte()):
            if not NOME_DE_ETAPA.match(linha):
                continue
            com_interpretador = {m.group(2) for m in interpretador.finditer(linha)}
            for rel in alvo.findall(linha):
                caminho = os.path.join(RAIZ, rel)
                if not os.path.exists(caminho):
                    faltando.append(rel)
                elif rel not in com_interpretador and not os.access(caminho, os.X_OK):
                    sem_bit.append(rel)
        self.assertEqual(faltando, [], f"etapa aponta para ferramenta inexistente: {faltando}")
        self.assertEqual(sem_bit, [], (
            f"ferramenta sem bit de execucao: {sem_bit} — o runner sairia 126 de madrugada "
            "e o ledger diria 'vermelho' sem apontar a fiacao"))

    def test_globs_de_descoberta_continuam_declarados(self):
        """Eles sao as raizes do censo de tools/check-detector-orfao."""
        texto = fonte()
        declarados = set(re.findall(r'for\s+\w+\s+in\s+"\$RAIZ"/(tools/[A-Za-z0-9_.*-]+)\s*;', texto))
        faltando = [g for g in GLOBS_ESPERADOS if g not in declarados]
        self.assertEqual(faltando, [], (
            f"glob de descoberta ausente: {faltando}. Cada um e' uma RAIZ do censo de "
            "detector orfao: sem ele, dezenas de detectores passam a parecer ligados "
            "(ou orfaos) sem que nada tenha mudado no produto"))

    def test_as_etapas_novas_da_travessia_estao_no_caminho_critico(self):
        """Controle positivo do proprio teste: ele tem de enxergar as etapas reais."""
        nomes = {m.group(2) for l in linhas_uteis(fonte()) for m in [NOME_DE_ETAPA.match(l)] if m}
        for etapa in ("detector-orfao", "gemea-espelha-public", "social-temas-404-tardio"):
            self.assertIn(etapa, nomes, f"a etapa {etapa} saiu do vigia")


if __name__ == "__main__":
    unittest.main(verbosity=2)
