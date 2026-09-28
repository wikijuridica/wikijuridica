#!/usr/bin/env python3
"""Todo gate que ABRE alerta ao dono tem de saber FECHÁ-LO.

POR QUE ESTA BANCADA EXISTE, com os números do dia
--------------------------------------------------
Em 2026-09-16 o painel do dono tinha TRÊS alertas abertos cuja causa já havia
sumido. Um deles estava aberto havia **263 horas** — e a própria evidência dele
dizia `home=200 pagina=200 sitemap=200 healthz=200 busca=200 servico=active`.

Duas causas distintas, a mesma classe de defeito:

1. `tools/check-portal-health` abria com CINCO chaves possíveis e resolvia
   SEMPRE com a chave fixa `portal-fora`. Quem abrisse como `redesocial-fora`
   nunca fechava.
2. `tools/check-efeito-nos-bots` só tinha o ramo de abertura
   (`if rc != 1: return`). Ficou 26 h aberto DEPOIS de o gate voltar a passar —
   e o que ele media nesse período era melhora: as páginas/dia do Googlebot
   subiram de 4,8 para 12,5.

Mais dois achados pela varredura desta bancada: `check-backup-restauravel` e
`check-untracked-e-alertar` também só abriam.

**O custo não é cosmético.** Alerta que nunca fecha ensina o dono a ignorar o
canal — e aí o próximo incidente de verdade chega no lugar exato onde ele parou
de olhar. Alarme que mente nos dois sentidos é pior que alarme nenhum, e este
mentia no sentido mais caro: dizer que há fogo onde não há.

O PREDICADO
-----------
Para cada ferramenta que invoca `notify-owner` com `--chave`, tem de existir no
mesmo arquivo um caminho com `--resolvido` (ou `resolvido=True`, na forma
Python). Ferramenta que apenas ANALISA units que chamam `notify-owner` é isenta,
por lista nomeada — e a lista exige o motivo escrito.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Isenções NOMEADAS, cada uma com o motivo. Não é allowlist de conveniência:
# quem entrar aqui tem de não emitir alerta próprio.
ISENTAS = {
    # Analisa units que CHAMAM notify-owner; as ocorrências são o alvo da
    # análise, não alerta próprio.
    "check-units-alarme": "analisa units que chamam notify-owner, não alerta",
    # É o próprio notificador.
    "notify-owner": "é o canal, não um consumidor dele",
    # Reconcilia o ledger; abre e fecha por conta do estado, não por veredito.
    "generate-alertas-reconciliados": "reconcilia o ledger inteiro, não emite veredito próprio",
    # Lê o ledger para reprovar; não abre alerta.
    "check-owner-alerts-abertos": "lê o ledger para reprovar, não abre alerta",
}

RE_ABRE = re.compile(r"--chave\b")
RE_RESOLVE = re.compile(r"--resolvido\b|resolvido\s*=\s*True|\"--resolvido\"|'--resolvido'")


def ferramentas_que_alertam() -> list[Path]:
    """Ferramentas rastreadas que invocam notify-owner com --chave."""
    proc = subprocess.run(
        ["git", "-C", str(RAIZ), "ls-files", "-z", "tools"],
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"git ls-files falhou: {proc.stderr.decode(errors='replace')}")

    achados = []
    for rel in proc.stdout.decode("utf-8", errors="replace").split("\0"):
        if not rel:
            continue
        caminho = RAIZ / rel
        if not caminho.is_file() or caminho.name.startswith("test_"):
            continue
        try:
            texto = caminho.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "notify-owner" in texto and RE_ABRE.search(texto):
            achados.append(caminho)
    return sorted(achados)


class TesteClasseDeDefeito(unittest.TestCase):
    def test_toda_ferramenta_que_abre_alerta_sabe_fechar(self):
        faltando = []
        for caminho in ferramentas_que_alertam():
            nome = caminho.name
            if nome in ISENTAS:
                continue
            texto = caminho.read_text(encoding="utf-8", errors="replace")
            if not RE_RESOLVE.search(texto):
                faltando.append(nome)
        self.assertEqual(
            faltando, [],
            "estas ferramentas abrem alerta e NÃO sabem fechá-lo — o alerta fica aberto "
            "depois de a causa sumir, e o painel do dono passa a mentir: %s" % faltando,
        )

    def test_os_dois_gates_do_incidente_resolvem(self):
        """Trava por nome os dois que custaram 263 h e 26 h."""
        for nome in ("check-portal-health", "check-efeito-nos-bots"):
            texto = (RAIZ / "tools" / nome).read_text(encoding="utf-8", errors="replace")
            with self.subTest(gate=nome):
                self.assertTrue(RE_RESOLVE.search(texto), f"{nome} voltou a só abrir alerta")

    def test_portal_health_nao_resolve_chave_fixa(self):
        """O defeito das 263 h: abrir com cinco chaves e fechar sempre uma.

        A resolução tem de derivar do que foi ABERTO — por isso o estado
        persiste as chaves. Se alguém voltar a fechar um literal fixo, isto cai.
        """
        texto = (RAIZ / "tools" / "check-portal-health").read_text(encoding="utf-8", errors="replace")
        # O campo EXATO no json.dump, não a substring: `"chaves_abertas_x"` contém
        # `chaves_abertas` e passaria. Medido em 2026-09-16 — o mutante que
        # renomeia o campo sobreviveu à primeira versão deste teste, e mutante
        # vivo denuncia o predicado, não o código.
        self.assertRegex(
            texto, r'"chaves_abertas"\s*:',
            "a chave aberta precisa persistir no estado com o nome exato "
            '`"chaves_abertas":`; sem isso a normalização não sabe o que fechar '
            "e volta a fechar uma chave fixa",
        )
        # E o estado tem de ser LIDO de volta, senão persistir não serve de nada.
        self.assertRegex(
            texto, r'get\("chaves_abertas"',
            "o estado persiste a chave mas ninguém a lê de volta",
        )
        # O literal "portal-fora" pode aparecer como fallback histórico, mas não
        # como ÚNICO argumento de um avisar_dono com resolvido=True.
        self.assertNotIn('avisar_dono("portal-fora", "info"', texto,
                         "a normalização voltou a fechar a chave fixa portal-fora")

    def test_isencoes_tem_motivo_escrito(self):
        """Allowlist sem motivo vira depósito. Cada isenção explica por quê."""
        for nome, motivo in ISENTAS.items():
            with self.subTest(ferramenta=nome):
                self.assertTrue(motivo and len(motivo) > 15,
                                f"a isenção de {nome} precisa do motivo escrito")

    def test_a_varredura_encontra_alguma_coisa(self):
        """Controle positivo: uma varredura que acha zero passaria sempre."""
        achadas = ferramentas_que_alertam()
        self.assertGreaterEqual(
            len(achadas), 5,
            "a varredura achou quase nada — provavelmente o padrão parou de casar, "
            "e aí este teste ficaria verde por vacuidade",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
