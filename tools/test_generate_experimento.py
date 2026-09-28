#!/usr/bin/env python3
"""Testes de tools/generate-experimento — fixtures numa raiz temporária, nunca
o ledger real (registrar um experimento de verdade ocupa o teto de 5% do acervo
e bloqueia as páginas para qualquer outro).

O que esta bancada trava, e como cada asserção reprova quando a linha some:
  - coorte DETERMINÍSTICA: mesmo path e mesmo sal caem sempre no mesmo braço,
    e trocar o sal reatribui — provado por MUTAÇÃO do sal, não por inspeção;
  - teto de 5% do acervo, somando experimentos ATIVOS — provado por MUTAÇÃO da
    constante (com o teto em 50% a coorte cresce, logo a constante é quem manda);
  - contrato de indexação: título de 20 a 65 caracteres e meta description de
    70 a 160 — provado por MUTAÇÃO do limite superior do título;
  - ética OAB: h1 com promessa de resultado nunca entra na coorte;
  - vocabulário interno reprovado E o falso positivo que ele já produziu
    (a palavra portuguesa "todo" casando com "TODO") permanentemente barrado;
  - DEC-017: todo texto de variante é recorte VERBATIM de texto autoral que já
    estava no estoque — a máquina não compõe frase nenhuma;
  - ensaio não cria o ledger; só `--aplicar` escreve.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERRAMENTA = os.path.join(RAIZ_REPO, "tools", "generate-experimento")
NUCLEO = os.path.join(RAIZ_REPO, "tools", "experimentos.py")

AREA = "familia"

# Temas reais de direito de família, para que o contrato de texto (tamanho,
# acento, promessa) seja exercitado sobre português de verdade.
TEMAS = [
    ("pensao-alimenticia-atraso", "Pensão alimentícia em atraso: o que fazer",
     "Quando a pensão atrasa, a execução pode seguir dois ritos distintos"),
    ("guarda-compartilhada-mudanca", "Guarda compartilhada e mudança de cidade",
     "A mudança de cidade não extingue a guarda compartilhada por si só"),
    ("uniao-estavel-prova", "União estável: como se prova no processo",
     "A prova da união estável se faz por documento, testemunha e contexto"),
    ("divorcio-cartorio-requisitos", "Divórcio em cartório: requisitos legais",
     "O divórcio extrajudicial exige consenso e ausência de menor incapaz"),
    ("partilha-bem-anterior", "Partilha de bem adquirido antes do casamento",
     "O bem anterior ao casamento pode ou não entrar na partilha"),
    ("alimentos-gravidicos", "Alimentos gravídicos: quem paga e quando",
     "Os alimentos gravídicos cobrem despesas da gestação desde a concepção"),
    ("regime-separacao-obrigatoria", "Regime de separação obrigatória de bens",
     "A separação obrigatória incide sobre quem casa depois dos setenta anos"),
    ("investigacao-paternidade-dna", "Investigação de paternidade e exame de DNA",
     "A recusa ao exame de DNA gera presunção relativa de paternidade"),
]


def _texto_com(n, base):
    """Frase em português com exatamente n caracteres DEPOIS de normalizada.

    O tamanho tem de valer sobre o texto normalizado porque é assim que
    `valida_titulo` mede. A primeira versão deste helper cortava em n e o corte
    caía num espaço, que `limpa()` remove — o "título de 66" chegava com 65 e
    passava. O teste do limite não testava limite nenhum.
    """
    recheio = " e o que a lei determina em cada caso concreto do processo judicial"
    texto = base
    while len(texto) < n:
        texto += recheio
    texto = texto[:n].rstrip()
    while len(texto) < n:
        texto += "s"
    return texto


def monta_raiz(quantas=40, extras=(), base_inerte=False):
    """Raiz temporária com manifesto e estoque v2 sintéticos, mais o tools/ real.

    `base_inerte=True` deixa as páginas de fundo INELEGÍVEIS para todos os
    fatores (h1 igual ao title, abre sem frase que caiba em 70–160, FAQ vazio).
    Serve aos testes de contrato de texto: o teto de 5% de um acervo de 400
    páginas é 20, então só com o fundo inerte é possível afirmar que uma página
    específica entrou ou não entrou na coorte por MÉRITO, e não por sorteio.
    """
    raiz = tempfile.mkdtemp(prefix="experimento-teste-")
    os.makedirs(os.path.join(raiz, "data", "editorial", "v2_pages"))
    os.symlink(os.path.join(RAIZ_REPO, "tools"), os.path.join(raiz, "tools"))

    manifesto = []
    estoque = []
    for indice in range(quantas):
        tema, titulo, abre = TEMAS[indice % len(TEMAS)]
        intent = f"fam-{tema}-{indice:03d}"
        caminho = f"/{AREA}/{tema}-{indice:03d}/"
        titulo_unico = f"{titulo} — caso {indice:03d}"
        h1 = titulo_unico if base_inerte else f"O que muda na {tema.replace('-', ' ')} no caso {indice:03d}"
        abertura = ("Frase curta. Outra curta." if base_inerte else
                    f"{abre} no caso {indice:03d}. O tribunal costuma exigir prova "
                    "documental antes de decidir. A parte contrária pode se manifestar.")
        perguntas = [] if base_inerte else [
            {"q": f"Quanto tempo demora no caso {indice:03d}?", "a": "Depende do rito e da comarca."},
            {"q": "Preciso de advogado?", "a": "Na via judicial, sim; no cartório, também."}]
        manifesto.append({"unique_intent_id": intent, "path": caminho,
                          "title": titulo_unico, "page_status": "published",
                          "index_policy": "index"})
        estoque.append({"intent_id": intent, "title": titulo_unico, "h1": h1,
                        "meta_description": f"Resumo objetivo sobre {tema} no caso {indice:03d} "
                                            "com o que a lei exige e o que o juiz costuma pedir.",
                        "opening": abertura,
                        "faq": perguntas,
                        "sections": [{"heading": "Como funciona", "text": abertura}]})

    for extra in extras:
        manifesto.append(extra["manifesto"])
        estoque.append(extra["estoque"])

    with open(os.path.join(raiz, "data", "editorial", "published_manifest.jsonl"),
              "w", encoding="utf-8") as handle:
        for registro in manifesto:
            handle.write(json.dumps(registro, ensure_ascii=False) + "\n")
    with open(os.path.join(raiz, "data", "editorial", "v2_pages", "familia-teste.jsonl"),
              "w", encoding="utf-8") as handle:
        for registro in estoque:
            handle.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return raiz


def pagina_extra(sufixo, titulo, h1, abre=None, faq=None, meta=None):
    intent = f"fam-extra-{sufixo}"
    caminho = f"/{AREA}/extra-{sufixo}/"
    abertura = abre or ("O juízo analisa o pedido à luz do Código Civil e do "
                        "Estatuto da Criança e do Adolescente. A decisão é fundamentada.")
    return {
        "manifesto": {"unique_intent_id": intent, "path": caminho, "title": titulo,
                      "page_status": "published", "index_policy": "index"},
        "estoque": {"intent_id": intent, "title": titulo, "h1": h1,
                    "meta_description": meta or (f"Página {sufixo} sobre direito de família com o "
                                                 "que a norma exige e o que costuma ser pedido."),
                    "opening": abertura,
                    "faq": faq if faq is not None else [],
                    "sections": [{"heading": "Ponto central", "text": abertura}]},
    }


def carrega(fonte_nucleo=None):
    """A ferramenta, opcionalmente sobre um NÚCLEO mutado.

    A mutação entra pelo `sys.modules`: a ferramenta faz
    `importlib.import_module("experimentos")` e recebe a versão alterada, sem
    que nenhum arquivo do repositório seja tocado.
    """
    guardado = sys.modules.get("experimentos")
    if fonte_nucleo is not None:
        nucleo = types.ModuleType("experimentos")
        nucleo.__file__ = NUCLEO
        exec(compile(fonte_nucleo, NUCLEO, "exec"), nucleo.__dict__)
        sys.modules["experimentos"] = nucleo
    try:
        ferramenta = types.ModuleType("generate_experimento_sob_teste")
        ferramenta.__file__ = FERRAMENTA
        with open(FERRAMENTA, encoding="utf-8") as handle:
            exec(compile(handle.read(), FERRAMENTA, "exec"), ferramenta.__dict__)
        return ferramenta
    finally:
        if fonte_nucleo is not None:
            if guardado is None:
                sys.modules.pop("experimentos", None)
            else:
                sys.modules["experimentos"] = guardado


def roda(ferramenta, *argumentos):
    saida = io.StringIO()
    with contextlib.redirect_stdout(saida), contextlib.redirect_stderr(saida):
        codigo = ferramenta.principal(list(argumentos))
    return codigo, saida.getvalue()


def ledger(raiz):
    caminho = os.path.join(raiz, "data", "ai", "experimentos.jsonl")
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8") as handle:
        return [json.loads(linha) for linha in handle if linha.strip()]


class TesteCoorte(unittest.TestCase):
    def setUp(self):
        self.raiz = monta_raiz(quantas=600)
        self.ferramenta = carrega()
        self.nucleo = sys.modules.get("experimentos") or __import__("experimentos")
        self.addCleanup(shutil.rmtree, self.raiz, True)

    def registro(self, *argumentos, raiz=None):
        alvo = raiz or self.raiz
        codigo, _ = roda(self.ferramenta, "--raiz", alvo, "--fator", "titulo",
                         "--area", AREA, "--aplicar", "--amostra", "0", *argumentos)
        self.assertEqual(codigo, 0)
        return ledger(alvo)[-1]

    def test_coorte_determinista_e_verificavel_pelo_hash(self):
        primeiro = self.registro("--id", "exp-a")
        segundo_raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, segundo_raiz, True)
        segundo = self.registro("--id", "exp-a", raiz=segundo_raiz)
        # reprova se: u_de() deixar de usar hashlib (com hash() do Python a
        # coorte muda a cada processo, que é o defeito que a R3 proíbe)
        self.assertEqual([i["path"] for i in primeiro["coorte"]],
                         [i["path"] for i in segundo["coorte"]])
        self.assertEqual([i["braco"] for i in primeiro["coorte"]],
                         [i["braco"] for i in segundo["coorte"]])
        # o braço de cada página é reproduzível por terceiro só com o sal
        sal = primeiro["aleatorizacao"]["sal"]
        bracos = [b["nome"] for b in primeiro["bracos"]]
        for item in primeiro["coorte"]:
            esperado, _u = self.nucleo.atribui_braco(sal, item["path"], bracos)
            # reprova se: atribui_braco() passar a sortear sem o sal
            self.assertEqual(item["braco"], esperado)
            # pertinência conferível pelo limiar gravado
            self.assertLessEqual(self.nucleo.u_de(sal, "selecao", item["path"]),
                                 primeiro["aleatorizacao"]["limiar_selecao"] + 1e-12)

    def test_sal_diferente_reatribui_as_paginas(self):
        caminhos = [f"/{AREA}/pagina-{i:04d}/" for i in range(500)]
        bracos = ["controle", "variante"]
        um = {p: self.nucleo.atribui_braco("sal-do-primeiro-sorteio", p, bracos)[0] for p in caminhos}
        dois = {p: self.nucleo.atribui_braco("sal-do-segundo-sorteio", p, bracos)[0] for p in caminhos}
        de_novo = {p: self.nucleo.atribui_braco("sal-do-primeiro-sorteio", p, bracos)[0] for p in caminhos}
        # reprova se: atribui_braco() virar sorteio com estado — o mesmo sal tem
        # de devolver a mesma divisão em qualquer processo, hoje e daqui a um ano
        self.assertEqual(um, de_novo)
        trocaram = sum(1 for p in caminhos if um[p] != dois[p])
        # reprova se: o sal sair do material do hash — sem ele DOIS experimentos
        # diferentes usariam a mesma divisão, e a segunda medição seria a
        # primeira amostra outra vez, com aparência de confirmação independente
        self.assertGreater(trocaram, 0.35 * len(caminhos))
        self.assertLess(trocaram, 0.65 * len(caminhos))
        equilibrio = sum(1 for p in caminhos if um[p] == "controle") / len(caminhos)
        self.assertTrue(0.42 < equilibrio < 0.58, f"braços desequilibrados: {equilibrio:.3f}")

    def test_teto_de_cinco_por_cento_do_acervo(self):
        raiz = monta_raiz(quantas=200)
        self.addCleanup(shutil.rmtree, raiz, True)
        registro = self.registro("--id", "exp-teto", raiz=raiz)
        self.assertEqual(registro["teto"]["paginas"], 10)
        # reprova se: `limite = min(len(elegiveis), disponivel)` deixar de
        # considerar o teto
        self.assertLessEqual(len(registro["coorte"]), 10)
        self.assertGreater(registro["elegibilidade"]["elegiveis"], 10,
                           "o teste só prova o teto se houver mais elegíveis do que ele")

    def test_mutacao_do_teto_muda_a_coorte(self):
        raiz = monta_raiz(quantas=200)
        self.addCleanup(shutil.rmtree, raiz, True)
        with open(NUCLEO, encoding="utf-8") as handle:
            fonte = handle.read()
        alvo = "TETO_FRACAO_ACERVO = 0.05"
        self.assertIn(alvo, fonte)
        mutante = carrega(fonte.replace(alvo, "TETO_FRACAO_ACERVO = 0.5"))
        codigo, _ = roda(mutante, "--raiz", raiz, "--fator", "titulo", "--area", AREA,
                         "--id", "exp-mutante", "--aplicar", "--amostra", "0")
        self.assertEqual(codigo, 0)
        # o mutante prova que a constante É quem limita: com 50% a coorte passa de 10
        self.assertGreater(len(ledger(raiz)[-1]["coorte"]), 10)

    def test_teto_e_global_entre_experimentos_ativos(self):
        raiz = monta_raiz(quantas=200)
        self.addCleanup(shutil.rmtree, raiz, True)
        self.registro("--id", "exp-primeiro", raiz=raiz)
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-segundo", "--aplicar", "--amostra", "0")
        # reprova se: `disponivel = teto_paginas - len(ocupadas)` virar teto por experimento
        self.assertEqual(codigo, 3)
        self.assertIn("teto global esgotado", saida)
        self.assertEqual(len(ledger(raiz)), 1, "experimento recusado não entra no ledger")

    def test_pagina_em_experimento_ativo_nao_entra_em_outro(self):
        raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, raiz, True)
        primeiro = self.registro("--id", "exp-um", "--paginas", "5", raiz=raiz)
        ocupadas = {i["path"] for i in primeiro["coorte"]}
        segundo = self.registro("--id", "exp-dois", "--paginas", "5", raiz=raiz)
        # reprova se: paginas_ocupadas() sair da elegibilidade — duas variantes
        # na mesma página tornam o desfecho ininterpretável
        self.assertFalse(ocupadas & {i["path"] for i in segundo["coorte"]})
        self.assertTrue(any(motivo.startswith("interferencia:")
                            for motivo in segundo["elegibilidade"]["recusas"]))

    def test_ensaio_nao_escreve_e_aplicar_escreve(self):
        codigo, saida = roda(self.ferramenta, "--raiz", self.raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-ensaio", "--amostra", "0")
        self.assertEqual(codigo, 0)
        self.assertIn("ENSAIO", saida)
        # reprova se: a escrita deixar de depender de `if args.aplicar`
        self.assertFalse(os.path.exists(os.path.join(self.raiz, "data", "ai", "experimentos.jsonl")),
                         "ensaio não pode nem criar o arquivo")
        self.registro("--id", "exp-ensaio")
        self.assertEqual(len(ledger(self.raiz)), 1)

    def test_id_repetido_e_recusado(self):
        self.registro("--id", "exp-unico")
        codigo, saida = roda(self.ferramenta, "--raiz", self.raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-unico", "--aplicar", "--amostra", "0")
        self.assertEqual(codigo, 4)
        self.assertIn("já existe experimento", saida)


class TesteCicloDeVida(unittest.TestCase):
    """As transições que fecham o ciclo: aplicar e encerrar.

    Sem elas o `aplicado_em` fica nulo para sempre (toda medição seria A/A) e
    as páginas de um experimento morto ocupariam o teto de 5% do acervo até
    alguém editar o ledger à mão — que é justamente o que o append-only proíbe.
    """

    def setUp(self):
        self.ferramenta = carrega()
        self.nucleo = sys.modules.get("experimentos") or __import__("experimentos")

    def cria(self, raiz, eid, **extra):
        argumentos = ["--raiz", raiz, "--fator", "titulo", "--area", AREA,
                      "--id", eid, "--aplicar", "--amostra", "0"]
        for chave, valor in extra.items():
            argumentos += ["--" + chave.replace("_", "-"), str(valor)]
        codigo, saida = roda(self.ferramenta, *argumentos)
        self.assertEqual(codigo, 0, saida)

    def test_marcar_aplicado_dobra_sobre_o_ledger(self):
        raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, raiz, True)
        self.cria(raiz, "exp-ciclo")
        codigo, saida = roda(self.ferramenta, "--raiz", raiz,
                             "--marcar-aplicado", "exp-ciclo", "--aplicado-em", "2026-09-15")
        self.assertEqual(codigo, 0)
        self.assertIn("ENSAIO", saida)
        # reprova se: a transição deixar de depender de --aplicar
        self.assertEqual(len(ledger(raiz)), 1, "ensaio de transição não escreve")
        codigo, _ = roda(self.ferramenta, "--raiz", raiz, "--marcar-aplicado", "exp-ciclo",
                         "--aplicado-em", "2026-09-15", "--aplicar")
        self.assertEqual(codigo, 0)
        vivos = self.nucleo.dobra_experimentos(ledger(raiz))
        # reprova se: dobra_experimentos() parar de dobrar `aplicado_em` — a
        # medição leria a linha de criação e devolveria A/A para sempre
        self.assertEqual(vivos["exp-ciclo"]["aplicado_em"], "2026-09-15")
        self.assertEqual(vivos["exp-ciclo"]["estado"], "aplicado")
        self.assertIn("exp-ciclo", self.nucleo.experimentos_ativos(ledger(raiz)))

    def test_encerrar_libera_as_paginas_do_teto(self):
        raiz = monta_raiz(quantas=200)
        self.addCleanup(shutil.rmtree, raiz, True)
        self.cria(raiz, "exp-primeiro")
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-segundo", "--aplicar", "--amostra", "0")
        self.assertEqual(codigo, 3, "com o teto cheio, o segundo tem de ser recusado")
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--encerrar", "exp-primeiro",
                             "--estado", "encerrado_descartado", "--motivo",
                             "variante sem efeito medido na janela", "--aplicar")
        self.assertEqual(codigo, 0, saida)
        self.assertNotIn("exp-primeiro", self.nucleo.experimentos_ativos(ledger(raiz)))
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-segundo", "--aplicar", "--amostra", "0")
        # reprova se: experimentos_ativos() parar de filtrar por ESTADOS_ATIVOS —
        # o acervo teria 5% preso em experimentos mortos
        self.assertEqual(codigo, 0, saida)

    def test_mutacao_que_ignora_a_transicao_mantem_o_teto_ocupado(self):
        raiz = monta_raiz(quantas=200)
        self.addCleanup(shutil.rmtree, raiz, True)
        self.cria(raiz, "exp-primeiro")
        roda(self.ferramenta, "--raiz", raiz, "--encerrar", "exp-primeiro",
             "--estado", "encerrado_adotado", "--aplicar")
        with open(NUCLEO, encoding="utf-8") as handle:
            fonte = handle.read()
        alvo = '        if registro.get("tipo") != "estado":'
        self.assertEqual(fonte.count(alvo), 1)
        mutante = carrega(fonte.replace(alvo, '        if registro.get("tipo") != "estado_que_nao_existe":'))
        codigo, _saida = roda(mutante, "--raiz", raiz, "--fator", "titulo", "--area", AREA,
                              "--id", "exp-segundo", "--aplicar", "--amostra", "0")
        # o mutante que ignora a linha de transição volta a recusar: prova que é
        # a dobra do ledger quem libera o teto
        self.assertEqual(codigo, 3)

    def test_nao_se_marca_aplicado_o_que_nao_tem_prosa(self):
        raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, raiz, True)
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--fator", "resumo_tres_linhas",
                             "--area", AREA, "--id", "exp-resumo", "--aplicar", "--amostra", "0")
        self.assertEqual(codigo, 0, saida)
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--marcar-aplicado", "exp-resumo",
                             "--aplicar")
        # reprova se: a guarda de prosa pendente sair — marcar como aplicado o
        # que ninguém escreveu é declarar no ar um texto que não existe
        self.assertEqual(codigo, 3)
        self.assertIn("sem prosa humana", saida)

    def test_transicao_de_experimento_inexistente_e_ledger_corrompido(self):
        raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, raiz, True)
        self.cria(raiz, "exp-existe")
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--encerrar", "exp-fantasma",
                             "--estado", "cancelado", "--aplicar")
        self.assertEqual(codigo, 3)
        self.assertIn("não está no ledger", saida)
        with open(os.path.join(raiz, "data", "ai", "experimentos.jsonl"), "a",
                  encoding="utf-8") as handle:
            handle.write("{isto nao e json}\n")
        codigo, saida = roda(self.ferramenta, "--raiz", raiz, "--fator", "titulo",
                             "--area", AREA, "--id", "exp-novo", "--aplicar", "--amostra", "0")
        # reprova se: o ValueError de le_ledger voltar a escapar como traceback —
        # experimento invisível liberaria as páginas dele para outro
        self.assertEqual(codigo, 2)
        self.assertIn("ledger ilegível", saida)


class TesteContratoDeTexto(unittest.TestCase):
    def monta(self, extras):
        raiz = monta_raiz(quantas=400, extras=extras, base_inerte=True)
        self.addCleanup(shutil.rmtree, raiz, True)
        return raiz

    def coorte(self, raiz, fator="titulo", ferramenta=None):
        alvo = ferramenta or carrega()
        codigo, saida = roda(alvo, "--raiz", raiz, "--fator", fator, "--area", AREA,
                             "--id", "exp-contrato", "--aplicar", "--amostra", "0")
        self.assertEqual(codigo, 0, saida)
        return ledger(raiz)[-1]

    def test_titulo_fora_de_20_a_65_nao_entra(self):
        longo = _texto_com(66, "Como o juízo decide a guarda quando os pais moram longe")
        curto = "Guarda e mudança"
        raiz = self.monta([pagina_extra("longo", "Título atual da página sobre guarda", longo),
                           pagina_extra("curto", "Título atual sobre alimentos e prova", curto),
                           pagina_extra("boa", "Título atual sobre bem de família e impenhorabilidade",
                                        "Quando o bem de família deixa de ser impenhorável")])
        registro = self.coorte(raiz)
        variantes = {i["path"]: i.get("texto_variante") for i in registro["coorte"]}
        self.assertNotIn(f"/{AREA}/extra-longo/", variantes)
        self.assertNotIn(f"/{AREA}/extra-curto/", variantes)
        recusas = registro["elegibilidade"]["recusas"]
        # reprova se: valida_titulo() deixar de conferir TITULO_MIN/TITULO_MAX
        self.assertGreaterEqual(recusas.get("titulo_longo", 0), 1)
        self.assertGreaterEqual(recusas.get("titulo_curto", 0), 1)
        for item in registro["coorte"]:
            if item.get("texto_variante"):
                self.assertTrue(20 <= len(item["texto_variante"]) <= 65)

    def test_mutacao_do_limite_do_titulo_admite_o_h1_longo(self):
        longo = _texto_com(66, "Como o juízo decide a guarda quando os pais moram longe")
        raiz = self.monta([pagina_extra("longo", "Título atual da página sobre guarda", longo)])
        with open(NUCLEO, encoding="utf-8") as handle:
            fonte = handle.read()
        alvo = "TITULO_MIN, TITULO_MAX = 20, 65"
        self.assertIn(alvo, fonte)
        mutante = carrega(fonte.replace(alvo, "TITULO_MIN, TITULO_MAX = 20, 80"))
        registro = self.coorte(raiz, ferramenta=mutante)
        paths = {i["path"] for i in registro["coorte"]}
        # com o limite frouxo o h1 de 66 caracteres passa: a constante é quem manda
        self.assertIn(f"/{AREA}/extra-longo/", paths)

    def test_promessa_de_resultado_nunca_entra(self):
        raiz = self.monta([
            pagina_extra("promessa", "Título atual sobre execução de alimentos",
                         "Garantimos a reversão da guarda em qualquer instância do processo"),
            pagina_extra("boa", "Título atual sobre bem de família e impenhorabilidade",
                                        "Quando o bem de família deixa de ser impenhorável")])
        registro = self.coorte(raiz)
        # reprova se: valida_titulo() deixar de chamar detect_promise
        self.assertNotIn(f"/{AREA}/extra-promessa/", {i["path"] for i in registro["coorte"]})
        self.assertTrue(any(motivo.startswith("promessa_oab:")
                            for motivo in registro["elegibilidade"]["recusas"]))

    def test_vocabulario_interno_barra_e_a_palavra_todo_passa(self):
        raiz = self.monta([
            pagina_extra("rascunho", "Título atual sobre partilha de bens",
                         "Rascunho do texto sobre partilha de bens do casal"),
            pagina_extra("todo", "Título atual sobre alimentos entre parentes",
                         "Nem todo acordo de alimentos precisa de homologação judicial"),
            pagina_extra("boa", "Título atual sobre bem de família e impenhorabilidade",
                                        "Quando o bem de família deixa de ser impenhorável"),
        ])
        registro = self.coorte(raiz)
        paths = {i["path"] for i in registro["coorte"]}
        # controle positivo: vocabulário interno de verdade reprova
        self.assertNotIn(f"/{AREA}/extra-rascunho/", paths)
        # REGRESSÃO MEDIDA: com re.IGNORECASE, "TODO" casava a palavra portuguesa
        # "todo" e reprovava 19 H1 legítimos do acervo real (2026-09-10)
        self.assertIn(f"/{AREA}/extra-todo/", paths)

    def test_unicidade_de_titulo_no_acervo_e_entre_variantes(self):
        ocupado = "Divórcio em cartório: requisitos legais — caso 003"
        raiz = self.monta([
            pagina_extra("colide-acervo", "Título atual sobre bem de família", ocupado),
            pagina_extra("gemea-a", "Título atual da primeira gêmea",
                         "Quando a pensão pode ser revista depois do acordo"),
            pagina_extra("gemea-b", "Título atual da segunda gêmea",
                         "Quando a pensão pode ser revista depois do acordo"),
        ])
        registro = self.coorte(raiz)
        paths = {i["path"] for i in registro["coorte"]}
        # reprova se: titulos_do_acervo sair de valida_titulo()
        self.assertNotIn(f"/{AREA}/extra-colide-acervo/", paths)
        gemeas = {f"/{AREA}/extra-gemea-a/", f"/{AREA}/extra-gemea-b/"} & paths
        # reprova se: `reivindicados` sumir — duas páginas com o MESMO título novo
        self.assertEqual(len(gemeas), 1)

    def test_meta_description_sai_de_frase_inteira_do_abre(self):
        sem_corte = pagina_extra("sem-corte", "Título atual sobre curatela",
                                 "Curatela e apoio", abre="Frase curta. Outra curta.")
        # Páginas com abre normal, para que exista o que medir ao lado da recusada.
        boas = [pagina_extra(
            f"abre-{i}", f"Título atual sobre tomada de decisão apoiada {i}",
            f"Tomada de decisão apoiada e seus limites no caso {i}",
            abre=(f"A tomada de decisão apoiada preserva a capacidade civil da pessoa no caso {i}. "
                  "O termo é levado a juízo com a assinatura dos apoiadores."))
            for i in range(6)]
        raiz = self.monta([sem_corte] + boas)
        registro = self.coorte(raiz, fator="meta_description")
        estoque = {}
        with open(os.path.join(raiz, "data", "editorial", "v2_pages", "familia-teste.jsonl"),
                  encoding="utf-8") as handle:
            for linha in handle:
                dado = json.loads(linha)
                estoque[dado["intent_id"]] = dado
        self.assertNotIn(f"/{AREA}/extra-sem-corte/", {i["path"] for i in registro["coorte"]})
        for item in registro["coorte"]:
            texto = item.get("texto_variante")
            if not texto:
                continue
            # reprova se: recorte_por_frase() cortar por caractere — o contrato
            # de 70 a 160 e a proibição de fragmento truncado são os dois
            self.assertTrue(70 <= len(texto) <= 160)
            abre = estoque[item["intent_id"]]["opening"]
            self.assertTrue(abre.startswith(texto), "a meta é prefixo literal do abre")
            self.assertTrue(texto.endswith((".", "!", "?")), "corte em fim de frase")

    def test_ordem_faq_permuta_sem_criar_pergunta(self):
        raiz = self.monta([
            pagina_extra("faq-zero", "Título atual sobre visitação", "Visitação e convivência familiar"),
            pagina_extra("faq-um", "Título atual sobre alienação parental",
                         "Alienação parental e as medidas do juízo",
                         faq=[{"q": "O que caracteriza?", "a": "Interferência na convivência."}]),
        ] + [pagina_extra(
            f"faq-boa-{i}", f"Título atual sobre convivência assistida {i}",
            f"Convivência assistida e o papel do acompanhante no caso {i}",
            faq=[{"q": f"Quem acompanha a visita no caso {i}?", "a": "Profissional designado pelo juízo."},
                 {"q": "Por quanto tempo dura?", "a": "Até a reavaliação técnica."},
                 {"q": "Pode ser revista?", "a": "Sim, a qualquer tempo, com fundamento."}])
            for i in range(6)])
        registro = self.coorte(raiz, fator="ordem_faq")
        paths = {i["path"] for i in registro["coorte"]}
        # reprova se: `if len(faq) < 2` sair — permutar 0 ou 1 pergunta é um no-op
        # que apareceria como braço "variante" idêntico ao controle
        self.assertNotIn(f"/{AREA}/extra-faq-zero/", paths)
        self.assertNotIn(f"/{AREA}/extra-faq-um/", paths)
        variante = [i for i in registro["coorte"] if i["braco"] != "controle"]
        self.assertTrue(variante)
        for item in variante:
            ordem = item["permutacao"]
            self.assertEqual(sorted(ordem), list(range(item["faq_n"])),
                             "é permutação: mesmas perguntas, nenhuma criada ou perdida")
            self.assertNotEqual(ordem, list(range(item["faq_n"])),
                                "a variante tem de diferir do controle")

    def test_resumo_de_tres_linhas_nasce_sem_prosa_e_bloqueado(self):
        raiz = self.monta([])
        registro = self.coorte(raiz, fator="resumo_tres_linhas")
        self.assertEqual(registro["estado"], "aguardando_prosa")
        self.assertTrue(registro["bloqueios"], "o estoque v2 não tem campo resumo")
        self.assertIn("BLOQUEADO", registro["comando_de_aplicacao"])
        for item in registro["coorte"]:
            # reprova se: alguém "preencher" o resumo automaticamente — é
            # exatamente a geração de prosa pública que a DEC-017 proíbe
            self.assertIsNone(item["texto_variante"])
        self.assertGreater(registro["pendencias"]["paginas_sem_prosa"], 0)


class TesteDec017(unittest.TestCase):
    """A máquina nunca inventa prosa: todo texto de variante é verbatim do estoque."""

    def test_todo_texto_de_variante_e_verbatim_do_estoque(self):
        raiz = monta_raiz(quantas=600)
        self.addCleanup(shutil.rmtree, raiz, True)
        ferramenta = carrega()
        estoque = {}
        with open(os.path.join(raiz, "data", "editorial", "v2_pages", "familia-teste.jsonl"),
                  encoding="utf-8") as handle:
            for linha in handle:
                dado = json.loads(linha)
                estoque[dado["intent_id"]] = dado
        for fator in ("titulo", "meta_description"):
            codigo, saida = roda(ferramenta, "--raiz", raiz, "--fator", fator, "--area", AREA,
                                 "--id", f"exp-dec017-{fator}", "--aplicar", "--amostra", "0",
                                 "--paginas", "6")
            self.assertEqual(codigo, 0, saida)
            registro = ledger(raiz)[-1]
            achou = 0
            for item in registro["coorte"]:
                texto = item.get("texto_variante")
                if not texto:
                    continue
                achou += 1
                fonte = estoque[item["intent_id"]]
                if fator == "titulo":
                    self.assertEqual(texto, fonte["h1"].strip())
                else:
                    self.assertTrue(fonte["opening"].startswith(texto))
            self.assertGreater(achou, 0, "o teste precisa de pelo menos uma variante")


if __name__ == "__main__":
    unittest.main(verbosity=2)
