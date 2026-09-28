#!/usr/bin/env python3
"""O classificador de lote tem de dizer POR QUE reprovou — sobre o acervo vivo.

Esta suíte existe porque um veredito sem motivo custou um dia inteiro de
diagnóstico errado (2026-09-05). ``classify_batch_completion`` reduzia cinco
cláusulas independentes a um bit; ``verify_v2_writing_queue_closure`` traduzia
o bit por "classificador não confirmou lote completo" e embrulhava em "lote
omitido sem shard completo". A frase se lê como "não há páginas escritas", e
foi assim que 34 lotes com o slice INTEIRO redigido — divergindo do pin só na
ordem das linhas — foram tratados como pendência de redação.

O que se protege NÃO é o defeito de hoje (``familia-03`` fora de ordem): esse
some no primeiro ``tools/generate-v2-shard-slice-reorder --apply``. O que se
protege é a INVARIANTE, sobre a topologia viva inteira:

    completion.complete  ⇔  completion.reasons == ()

e a fidelidade de cada motivo a uma recontagem independente, derivada dos
mesmos bytes por um caminho que não usa o classificador. Enquanto houver lote
reprovado no inventário, esta suíte compara motivo a motivo; quando não houver
mais nenhum, ela ainda cobra a invariante sobre os lotes completos e sobre os
casos sintéticos de fronteira.
"""
from __future__ import annotations

import collections
import pathlib
import sys
import unittest
from typing import Any, Mapping

_IMPORT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(_IMPORT_ROOT))

from tools import audit_v2_pages as auditor
from tools import generate_v2_review_queue as producer
from tools import verify_v2_writing_queue_closure as closure

# Derivado de __file__ como todos os irmaos de tools/: com a raiz cravada, um
# ensaio rodaria o codigo da copia contra o dado de producao.
_RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _inventario_vivo() -> tuple[dict[str, Any], set[str]]:
    integral, _ = closure._static_batches(
        _RAIZ / "scripts/workflows/writing-mass-full.js",
        max_bytes=closure._MAX_FULL_WORKFLOW_BYTES, require_nonempty=True)
    fila, _ = closure._static_batches(
        _RAIZ / "scripts/workflows/writing-mass-todo.js",
        max_bytes=closure._MAX_TODO_WORKFLOW_BYTES, require_nonempty=False)
    por_slug: dict[str, Any] = {}
    for indice, lote in enumerate(integral, 1):
        por_slug[closure._validate_base_batch(lote, f"lote {indice}")] = lote
    return por_slug, {lote.get("slug") for lote in fila}


class ClassificadorExplicaSobreOAcervoVivo(unittest.TestCase):
    """Percorre TODO lote omitido da fila e cobra motivo por bytes reais."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.por_slug, cls.na_fila = _inventario_vivo()
        cls.cache: dict = {}
        cls.contexto = closure._working_directory(_RAIZ)
        cls.contexto.__enter__()
        cls.contrato = producer.load_writing_semantic_contract(_RAIZ)
        cls.vencedores, _ = (
            auditor.validated_duplicate_supersession_winners(_RAIZ))
        cls.casos: list[tuple[str, Any, list[str], list[Mapping[str, Any]]]] = []
        for slug, lote in cls.por_slug.items():
            if slug in cls.na_fila:
                continue
            alvo = _RAIZ / f"data/editorial/v2_pages/{slug}.jsonl"
            if not alvo.exists():
                continue
            _, _, por_familia = closure._portfolio_records(
                _RAIZ, lote["file"], cls.cache)
            esperado = closure._expected_intents(lote, por_familia)
            instantaneo = producer.read_regular_file_snapshot(
                alvo, max_bytes=closure._MAX_TARGET_BYTES)
            registros = closure._decode_jsonl_strict(
                instantaneo.payload, f"data/editorial/v2_pages/{slug}.jsonl")
            cls.casos.append((slug, lote, esperado, registros))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.contexto.__exit__(None, None, None)

    def _classifica(self, slug, esperado, registros):
        bloqueadas = producer.semantic_blocked_for_batch(
            esperado, self.contrato)
        return producer.classify_batch_completion(
            registros, esperado, f"{slug}.jsonl", self.vencedores,
            semantically_blocked_intents=bloqueadas), set(bloqueadas)

    def test_topologia_viva_tem_lote_bastante_para_a_prova(self):
        """Suíte que roda sobre zero lote não prova nada — falhe alto."""
        self.assertGreaterEqual(
            len(self.casos), 1,
            "nenhum lote omitido com shard no disco: a prova ficou vazia")

    def test_veredito_e_motivo_nunca_se_contradizem(self):
        """``complete`` ⇔ ``reasons`` vazio, em cada lote vivo."""
        contradicoes = []
        for slug, _lote, esperado, registros in self.casos:
            try:
                completion, _ = self._classifica(slug, esperado, registros)
            except ValueError:
                # Lote que o classificador RECUSA (extra sem supersessão
                # autenticada) não produz veredito nenhum: é outra classe,
                # coberta pelas suítes de DEC-020, e não afrouxa esta.
                continue
            if completion.complete != (not completion.reasons):
                contradicoes.append(
                    f"{slug}: complete={completion.complete} "
                    f"reasons={completion.reasons}")
        self.assertEqual([], contradicoes)

    def test_todo_lote_reprovado_diz_o_que_falta(self):
        """Nenhum lote vivo pode reprovar com motivo vazio."""
        mudos = []
        for slug, _lote, esperado, registros in self.casos:
            try:
                completion, _ = self._classifica(slug, esperado, registros)
            except ValueError:
                continue
            if not completion.complete and not completion.reasons:
                mudos.append(slug)
        self.assertEqual([], mudos)

    def test_cada_motivo_bate_com_recontagem_independente(self):
        """Recontagem pelos MESMOS bytes, por caminho que não usa o classificador."""
        divergencias = []
        for slug, _lote, esperado, registros in self.casos:
            try:
                completion, bloqueadas = self._classifica(
                    slug, esperado, registros)
            except ValueError:
                continue
            if completion.complete:
                continue
            observado = [registro.get("intent_id") for registro in registros]
            ocorrencias = collections.Counter(
                iid for iid in observado if iid in set(esperado))
            faltantes = [iid for iid in esperado if iid not in ocorrencias]
            duplicados = [iid for iid in esperado
                          if ocorrencias.get(iid, 0) > 1]
            preenchidos = set()
            for registro in registros:
                iid = registro.get("intent_id")
                if iid not in set(esperado) or iid in bloqueadas:
                    continue
                razao = registro.get("skip_reason")
                if (registro.get("skipped") and isinstance(razao, str) and
                        razao.strip()):
                    preenchidos.add(iid)
                elif producer.writing_reusable_page(registro):
                    preenchidos.add(iid)
            bloqueados_presentes = [
                iid for iid in esperado
                if iid in ocorrencias and iid in bloqueadas]
            sem_corpo = [
                iid for iid in esperado
                if iid in ocorrencias and iid not in bloqueadas and
                iid not in preenchidos]
            juntos = "; ".join(completion.reasons)

            def cobra(condicao: bool, chave: str, quantidade: int) -> None:
                marca = f"{chave}={quantidade}"
                if condicao and marca not in juntos:
                    divergencias.append(f"{slug}: faltou {marca} em {juntos!r}")
                if not condicao and f"{chave}=" in juntos:
                    divergencias.append(f"{slug}: sobrou {chave} em {juntos!r}")

            cobra(bool(faltantes), "linha_faltante", len(faltantes))
            cobra(bool(duplicados), "intent_duplicado", len(duplicados))
            cobra(bool(bloqueados_presentes), "bloqueio_semantico",
                  len(bloqueados_presentes))
            cobra(bool(sem_corpo), "corpo_nao_reusavel", len(sem_corpo))

            canonico = (tuple(esperado) +
                        tuple(completion.authenticated_extras))
            multiconjunto_bate = (
                not faltantes and not duplicados and
                len(registros) == len(canonico))
            ordem_diverge = (multiconjunto_bate and
                             tuple(observado) != canonico)
            if ordem_diverge:
                posicoes = sum(1 for a, b in zip(observado, canonico) if a != b)
                if f"ordem_divergente={posicoes}" not in juntos:
                    divergencias.append(
                        f"{slug}: faltou ordem_divergente={posicoes} em {juntos!r}")
            elif "ordem_divergente" in juntos:
                divergencias.append(
                    f"{slug}: ordem_divergente indevido em {juntos!r}")
        self.assertEqual([], divergencias)

    def test_ordem_divergente_nunca_convive_com_falta_de_linha(self):
        """O motivo de ordem só sai quando o multiconjunto já bate.

        Anunciar ``ordem_divergente`` num lote a que falta página mandaria o
        operador rodar a permutação mecânica sobre um shard que precisa de
        redator — e a permutação recusaria, gastando a rodada.
        """
        erros = []
        for slug, _lote, esperado, registros in self.casos:
            try:
                completion, _ = self._classifica(slug, esperado, registros)
            except ValueError:
                continue
            juntos = "; ".join(completion.reasons)
            if "ordem_divergente" in juntos and "linha_faltante" in juntos:
                erros.append(f"{slug}: {juntos}")
        self.assertEqual([], erros)

    def test_dica_mecanica_so_em_lote_que_o_predicado_mecanico_aceita(self):
        """Sobre o acervo vivo: encaminhar para ferramenta que recusa é bug.

        ``tools/generate-v2-shard-slice-reorder`` exige
        ``writing_recovery_mechanical_only``, que reprova lote com extra
        DEC-020 e lote com intenção que não preenche. Este teste cobra a
        implicação sobre TODOS os lotes vivos: se a mensagem cita a ferramenta,
        o predicado tem de aceitar o lote.
        """
        mal_encaminhados = []
        for slug, _lote, esperado, registros in self.casos:
            try:
                completion, bloqueadas = self._classifica(
                    slug, esperado, registros)
            except ValueError:
                continue
            juntos = "; ".join(completion.reasons)
            if "generate-v2-shard-slice-reorder" not in juntos:
                continue
            if completion.authenticated_extras:
                mal_encaminhados.append(
                    f"{slug}: {len(completion.authenticated_extras)} extra(s) "
                    f"DEC-020 e a mensagem manda reordenar")
            if set(esperado) & bloqueadas:
                mal_encaminhados.append(
                    f"{slug}: intenção bloqueada e a mensagem manda reordenar")
        self.assertEqual([], mal_encaminhados)


class MotivoNosCasosDeFronteira(unittest.TestCase):
    """Casos sintéticos que o acervo vivo pode não conter hoje.

    Não substituem a prova sobre a topologia viva: cobrem as cláusulas que
    hoje não têm exemplar (duplicata, extra autenticado, corpo não reusável) e
    são os CONTROLES — se qualquer um destes passar a aprovar, o motivo virou
    afrouxamento de gate.
    """

    def test_lote_completo_nao_tem_motivo(self):
        registros = [
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=())
        self.assertTrue(completion.complete)
        self.assertEqual((), completion.reasons)

    def test_intrusa_no_slice_e_nomeada_em_vez_de_virar_ordem(self):
        """A cláusula 1 é igualdade de CONJUNTOS, e os dois lados são cobertos.

        ``set(occurrences) - expected`` é inalcançável hoje, porque só o ramo
        ``iid in expected`` incrementa ``occurrences``. O motivo existe para o
        dia em que uma refatoração afrouxar aquele ramo: sem ele, a cláusula 1
        passaria a falhar por uma linha indevida e a função — olhando só
        ``expected_order`` — atribuiria a falha a ``ordem_divergente``,
        mandando reordenar um shard que ganhou conteúdo que não é dele.

        Chamado direto na função pura porque o caminho público não consegue
        produzir o estado, e um teste que não consegue construir o caso é um
        teste que não trava nada.
        """
        razoes = producer._batch_completion_reasons(
            expected_order=("a", "b"),
            expected={"a", "b"},
            occurrences={"a": 1, "b": 1, "intrusa": 1},
            filled={"a", "b"},
            semantically_blocked=set(),
            observed_order=("a", "b"),
            extras=(),
            total=2,
        )
        self.assertTrue(any(r.startswith("intent_fora_do_slice=1") for r in razoes),
                        razoes)
        self.assertFalse(any("ordem_divergente" in r for r in razoes), razoes)

    def test_slice_coerente_nao_inventa_intrusa(self):
        """Controle: com os conjuntos coerentes, o motivo novo fica calado."""
        razoes = producer._batch_completion_reasons(
            expected_order=("a", "b"),
            expected={"a", "b"},
            occurrences={"a": 1, "b": 1},
            filled={"a", "b"},
            semantically_blocked=set(),
            observed_order=("a", "b"),
            extras=(),
            total=2,
        )
        self.assertEqual((), tuple(razoes))

    def test_duplicata_reprova_e_e_nomeada(self):
        registros = [
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=())
        self.assertFalse(completion.complete)
        self.assertIn("intent_duplicado=1", "; ".join(completion.reasons))

    def test_corpo_vazio_reprova_e_e_nomeado(self):
        registros = [
            {"intent_id": "a", "sections": []},
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=())
        self.assertFalse(completion.complete)
        self.assertIn("corpo_nao_reusavel=1", "; ".join(completion.reasons))

    def test_ordem_trocada_reprova_e_aponta_a_linha(self):
        registros = [
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=())
        self.assertFalse(completion.complete)
        juntos = "; ".join(completion.reasons)
        self.assertIn("ordem_divergente=2 de 2", juntos)
        # A frase passou a numerar a PINADA, e não a linha do arquivo
        # (2026-09-10): com extra DEC-020 ancorado no meio do shard, "linha N"
        # apontava para uma posição que o operador não pode mexer.
        self.assertIn("a 1ª pinada", juntos)
        self.assertIn("'b' onde o pin manda 'a'", juntos)

    def test_extra_autenticado_fora_do_sufixo_nao_reprova_o_lote(self):
        """O extra DEC-020 ancorado no meio do shard NÃO é ordem divergente.

        SUPERA, em 2026-09-10, o teste anterior desta posição — que cobrava
        ``ordem_divergente=3 de 3`` para exatamente este arranjo. O motivo do
        anterior nunca foi escrito; o layout "extras no sufixo" era o que
        ``tools/generate-v2-shard-slice-reorder`` PRODUZ, e virou regra de
        aceitação sem decisão.

        O que o medimos custou uma escrita revertida: o registro de arquivo
        DEC-020 fixa ``source_line``, ``canonical_line`` e
        ``source_shard_sha256`` (``audit_v2_pages.py:24425-24439``). Mover a
        linha do extra invalida a atestação — e foi o que aconteceu ao permutar
        ``imobiliario-22`` à mão: ``validated_duplicate_supersession_winners``
        foi de 0 a 2 ``archive_record_metadata_invalid``. Exigir o sufixo era
        exigir a migração que a atestação proíbe.

        O contrato que fica: as PINADAS na ordem do pin, lidas sem os extras.
        """
        registros = [
            {"intent_id": "extra", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", {("x.jsonl", "extra")},
            semantically_blocked_intents=())
        self.assertTrue(completion.complete, completion.reasons)
        self.assertEqual((), tuple(completion.reasons))
        self.assertEqual(("extra",), completion.authenticated_extras)

    def test_pinada_trocada_com_extra_ancorado_continua_reprovando(self):
        """MUTAÇÃO da regra acima: ignorar a posição do extra não pode cegar
        a ordem das pinadas entre si.

        Mesmo shard do teste anterior, com 'a' e 'b' trocadas: o extra segue
        ancorado no meio e o lote TEM de reprovar, porque agora a divergência é
        das intenções pinadas — a única coisa que o pin governa.
        """
        registros = [
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "extra", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", {("x.jsonl", "extra")},
            semantically_blocked_intents=())
        self.assertFalse(completion.complete)
        juntos = "; ".join(completion.reasons)
        self.assertIn("ordem_divergente=2 de 2 posicao(oes) do pin", juntos)
        self.assertIn("o shard tem 3 linha(s) contando os extras", juntos)
        self.assertNotIn("linha_faltante", juntos)

    def test_extra_dec020_nao_e_encaminhado_a_reordenacao_mecanica(self):
        """CONTROLE: a permutação mecânica RECUSA lote com extra DEC-020.

        Medido em 2026-09-05: ``imobiliario-10`` (9 do slice + 8 extras) e
        ``imobiliario-22`` (12 + 2) levantam
        ``writing_raw_recovery_valid_extra_requires_migration`` em
        ``capture_writing_raw_recovery_projection``, e
        ``writing_recovery_mechanical_only`` devolve False. Prometer
        "permutacao pura, zero redacao" nesses dois manda o operador a uma
        ferramenta que aborta — que é a classe de erro que este motivo existe
        para eliminar, não para reproduzir com outra frase.
        """
        registros = [
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "extra", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
        ]
        juntos = "; ".join(producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", {("x.jsonl", "extra")},
            semantically_blocked_intents=()).reasons)
        self.assertNotIn("generate-v2-shard-slice-reorder", juntos)
        self.assertIn("ancorado(s) por linha", juntos)
        self.assertIn(
            "writing_raw_recovery_valid_extra_requires_migration", juntos)

    def test_so_o_lote_puramente_permutado_ganha_a_dica_mecanica(self):
        """CONTROLE simétrico: sem extra e sem bloqueio, a dica TEM de sair."""
        registros = [
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
        ]
        juntos = "; ".join(producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=()).reasons)
        self.assertIn("tools/generate-v2-shard-slice-reorder", juntos)

    def test_bloqueio_semantico_com_ordem_trocada_nao_promete_permutacao(self):
        """CONTROLE: os 4 lotes que são bloqueio semântico E ordem divergente.

        ``glossario-01`` (2 bloqueios), ``glossario-02`` (3), ``glossario-11``
        (1) e ``glossario2-15`` (1) têm o conjunto inteiro no shard e a ordem
        divergente, mas ``writing_recovery_mechanical_only`` devolve False
        enquanto houver intenção bloqueada: reordenar não os fecha.
        """
        registros = [
            {"intent_id": "b", "sections": [{"heading": "h", "text": "t"}]},
            {"intent_id": "a", "sections": [{"heading": "h", "text": "t"}]},
        ]
        juntos = "; ".join(producer.classify_batch_completion(
            registros, ["a", "b"], "x.jsonl", (),
            semantically_blocked_intents=("a",)).reasons)
        self.assertIn("bloqueio_semantico=1", juntos)
        self.assertIn("ordem_divergente", juntos)
        self.assertNotIn("generate-v2-shard-slice-reorder", juntos)
        self.assertIn("reordenar NAO basta", juntos)

    def test_substituicao_integral_tem_motivo_proprio(self):
        registros = [
            {"intent_id": "velho-1",
             "sections": [{"heading": "h", "text": "t"}]},
        ]
        completion = producer.classify_batch_completion(
            registros, ["novo-1"], "x.jsonl", (),
            authenticated_replacement_intents=["velho-1"],
            semantically_blocked_intents=())
        self.assertFalse(completion.complete)
        self.assertEqual(
            ("substituicao_integral_autenticada",), completion.reasons)


if __name__ == "__main__":
    unittest.main()
