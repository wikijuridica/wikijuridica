#!/usr/bin/env python3
"""Testes de `tools/check-requirements-fixados`.

O risco deste gate e dizer que o ambiente esta fiel quando nao esta — e ele ja
errou nos DOIS sentidos, o que e a razao de a bancada cobrir os dois:

  1. anunciou 22 divergencias que nao existiam, por ler a versao errada dentro
     do proprio interpretador (`md.distributions()` sobre todo o `sys.path`);
  2. anunciou 5 divergencias das quais 4 eram falsas, por ler o INTERPRETADOR
     errado — o python3 do sistema no lugar do venv que serve aquele arquivo.

Os dois defeitos tem caso nomeado aqui, e cada caso diz a mutacao que o mata.
"""

from __future__ import annotations

import importlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import types
import unittest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
ALVO = RAIZ / "tools" / "check-requirements-fixados"
MAPA = RAIZ / "tools" / "requirements_interpretadores.json"

# Carrega compilando a fonte, sem passar por bytecode: `tools/` nao tem `.py`,
# o CPython grava `.pyc` assim mesmo e `SourceFileLoader` os revalida por
# (mtime em segundos, tamanho em bytes) — uma mutacao que PERMUTA preserva o
# tamanho e o loader serve o codigo velho. Ver
# tools/test_bytecode_obsoleto_cega_teste_de_ferramenta.py.
sys.dont_write_bytecode = True


def carrega():
    modulo = types.ModuleType("gate_requirements")
    modulo.__file__ = str(ALVO)
    exec(compile(ALVO.read_text(encoding="utf-8"), str(ALVO), "exec"),
         modulo.__dict__)
    return modulo


class BaseGate(unittest.TestCase):
    def setUp(self):
        self.gate = carrega()
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = pathlib.Path(self._tmp.name)
        (self.raiz / "tools").mkdir()
        # Toda raiz sintetica nasce com o mapa, porque sem entrada o gate
        # reprova por `sem_mapa` — que e o guarda contra apodrecimento e tem
        # caso proprio em test_requirements_sem_entrada_no_mapa_reprova.
        self.mapa = {}
        self.declara("requirements-teste.txt", sistema="sempre")

    def tearDown(self):
        self._tmp.cleanup()

    def declara(self, nome, *, venv_persistente="", venv_legado="",
                variavel_python="", variavel_venv="", sistema="nunca",
                materializar="comando de teste"):
        self.mapa[f"tools/{nome}"] = {
            "venv_persistente": venv_persistente,
            "venv_legado": venv_legado,
            "variavel_venv": variavel_venv,
            "variavel_python": variavel_python,
            "sistema": sistema,
            "materializar": materializar,
            "prova": "sintetico do teste",
        }
        (self.raiz / "tools" / "requirements_interpretadores.json").write_text(
            json.dumps({"arquivos": self.mapa}, ensure_ascii=False),
            encoding="utf-8")

    def escreve(self, nome: str, linhas: list[str]) -> None:
        (self.raiz / "tools" / nome).write_text(
            "\n".join(linhas) + "\n", encoding="utf-8")

    def venv_com(self, nome_dir: str, pacote: str, versao: str) -> str:
        """Cria um venv REAL e planta nele uma distribuicao com `versao`.

        Venv de verdade, nao diretorio imitado: e assim que `bin/python` nasce
        como SYMLINK para o binario do sistema, que e a condicao exata do
        defeito que `test_symlink_do_venv_nao_faz_o_gate_medir_o_sistema`
        reproduz. Custa 0,22 s medidos.
        """
        venv = self.raiz / nome_dir
        subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(venv)],
                       check=True, capture_output=True)
        site = next(venv.glob("lib/python*/site-packages"))
        info = site / f"{pacote}-{versao}.dist-info"
        info.mkdir()
        (info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {pacote}\nVersion: {versao}\n",
            encoding="utf-8")
        (info / "RECORD").write_text("", encoding="utf-8")
        return nome_dir


class TestRequirementsFixados(BaseGate):
    def test_versao_que_bate_passa(self):
        import importlib.metadata as md
        viva = md.version("pip")
        self.escreve("requirements-teste.txt", [f"pip=={viva}"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(estado["fixacoes"], 1)

    def test_versao_divergente_reprova_e_nomeia(self):
        self.escreve("requirements-teste.txt", ["pip==0.0.1-inexistente"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(len(estado["divergencias"]), 1)
        item = estado["divergencias"][0]
        self.assertEqual(item["pacote"], "pip")
        self.assertEqual(item["fixada"], "0.0.1-inexistente")
        self.assertNotEqual(item["viva"], "0.0.1-inexistente")
        self.assertEqual(item["interpretador"], "python3 do sistema")
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 1)

    def test_pacote_ausente_e_inventario_e_NAO_reprova(self):
        """Ausencia nao reprova, e a distincao e o desenho.

        O gate especifico de cada oraculo ja acusa a ferramenta ausente com a
        mensagem certa — `ptbr-morphsyntax-evidence` chega a imprimir o comando
        de provisionamento. Reprovar aqui duplicaria aquele vermelho e criaria
        um segundo lugar para desligar a mesma coisa.

        Mutacao que mata este caso: mover a ausencia para `divergencias`.
        """
        self.escreve("requirements-teste.txt",
                     ["pacote-que-nao-existe-em-lugar-nenhum==1.0.0"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(len(estado["ausencias"]), 1)
        self.assertEqual(estado["ausencias"][0]["pacote"],
                         "pacote-que-nao-existe-em-lugar-nenhum")
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 0)

    def test_le_a_versao_QUE_O_IMPORT_VE_e_nao_a_de_outro_sys_path(self):
        """O primeiro defeito deste gate, reproduzido.

        Montar o inventario com `md.distributions()` enumera TODOS os caminhos
        de `sys.path` — inclusive `/usr/lib/python3/dist-packages`, onde o
        Debian guarda copias antigas — e o ultimo achado sobrescrevia o
        primeiro. O gate anunciou `nltk 3.8` e `matplotlib 3.6.3` enquanto o
        `import` do mesmo interpretador entregava 3.9.4 e 3.11.0.

        Aqui planto uma distribuicao sintetica num caminho de MENOR precedencia
        e exijo que o gate continue reportando a de MAIOR — que e a que o codigo
        carregaria.

        Mutacao que mata este caso: voltar a montar dicionario com
        `md.distributions()`.
        """
        import importlib.metadata as md
        viva = md.version("pip")
        sombra = self.raiz / "sombra"
        info = sombra / "pip-0.0.0-sombra.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: pip\nVersion: 0.0.0-sombra\n",
            encoding="utf-8")
        (info / "RECORD").write_text("", encoding="utf-8")

        self.escreve("requirements-teste.txt", [f"pip=={viva}"])
        original = list(sys.path)
        try:
            # APPEND, nao insert: menor precedencia, como o dist-packages do
            # sistema costuma estar.
            sys.path.append(str(sombra))
            importlib.invalidate_caches()
            estado = self.gate.confere(str(self.raiz))
        finally:
            sys.path[:] = original
            importlib.invalidate_caches()
        self.assertEqual(estado["divergencias"], [],
                         "o gate leu a distribuicao de menor precedencia")

    def test_comentario_na_linha_do_pin_nao_vira_ausencia(self):
        """`pacote==1.0  # motivo` e a forma que os requirements deste repo usam.

        Sem cortar o comentario, a linha inteira falha o casamento de
        `nome==versao` e o pin some do conjunto conferido — o gate passaria a
        verde por nao ver a fixacao, que e a pior forma de passar.

        Mutacao que mata este caso: parar de cortar em `#`.
        """
        import importlib.metadata as md
        self.escreve("requirements-teste.txt",
                     ["# cabecalho inteiro comentado",
                      "pip==0.0.1-inexistente  # divergencia proposital",
                      f"python-dateutil=={md.version('python-dateutil')}"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["fixacoes"], 2, "o pin comentado sumiu do conjunto")
        self.assertEqual(len(estado["divergencias"]), 1)
        self.assertEqual(estado["divergencias"][0]["pacote"], "pip")
        self.assertEqual(estado["divergencias"][0]["fixada"], "0.0.1-inexistente")
        self.assertEqual(estado["ausencias"], [])

    def test_json_devolve_o_estado_inteiro(self):
        self.escreve("requirements-teste.txt", ["pip==0.0.1-inexistente"])
        saida = subprocess.run(
            [sys.executable, str(ALVO), "--json", "--raiz", str(self.raiz)],
            capture_output=True, text=True)
        self.assertEqual(saida.returncode, 1)
        estado = json.loads(saida.stdout)
        self.assertEqual(len(estado["divergencias"]), 1)
        self.assertIn("fixacoes", estado)
        self.assertIn("nao_provisionados", estado)

    def test_pontuacao_do_nome_nao_inventa_ausencia(self):
        """PEP 503: `-`, `_` e `.` sao equivalentes no nome de distribuicao.

        `lxml_html_clean` no requirements e `lxml-html-clean` instalado sao o
        mesmo pacote; ler como ausente seria falso vermelho por pontuacao.
        """
        import importlib.metadata as md
        viva = md.version("python-dateutil")
        self.escreve("requirements-teste.txt", [f"python_dateutil=={viva}"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(estado["ausencias"], [])


class TestInterpretadorCerto(BaseGate):
    """O segundo defeito: medir o interpretador ao lado.

    Estes quatro casos separam exatamente as duas metades do achado de
    2026-09-10 — o pin satisfeito no venv que o gate acusava por olhar o
    sistema, e o pin violado no interpretador que de fato roda.
    """

    def test_pin_satisfeito_no_venv_NAO_reprova_por_causa_do_sistema(self):
        """`trafilatura` e `torch`: o venv tem o pin, o sistema tem outra coisa.

        Sem fallback declarado, o sistema nao executa esses pins e a versao
        dele nao e assunto. Foi por ignorar isso que o gate anunciou 4
        divergencias falsas.

        Mutacao que mata este caso: medir `sys.executable` mesmo com
        `sistema: "nunca"`.
        """
        import importlib.metadata as md
        do_sistema = md.version("pip")
        self.assertNotEqual(do_sistema, "9.9.9")
        venv = self.venv_com("venv-do-arquivo", "pip", "9.9.9")
        self.declara("requirements-teste.txt", venv_persistente=venv,
                     sistema="nunca")
        self.escreve("requirements-teste.txt", ["pip==9.9.9"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [],
                         "o gate mediu o sistema para um pin que e do venv")
        self.assertEqual(estado["nao_provisionados"], [])
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 0)

    def test_pin_violado_no_interpretador_que_RODA_reprova(self):
        """`torch` em `requirements-oss-install-matrix.txt`, o caso real.

        O venv `.cache/oss-python-venv` nao esta provisionado e os consumidores
        Go declaram o fallback para o python3 do sistema
        (`internal/ossinstallmatrix/matrix.go:1952-1968`). Ali o sistema E o
        interpretador que roda, e divergencia nele e vermelho legitimo.

        Mutacao que mata este caso: tratar venv ausente como "nada a conferir"
        mesmo quando ha fallback declarado.
        """
        self.declara("requirements-teste.txt",
                     venv_persistente="venv-que-ninguem-criou",
                     sistema="quando_sem_venv")
        self.escreve("requirements-teste.txt", ["pip==0.0.1-inexistente"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(len(estado["divergencias"]), 1)
        self.assertEqual(estado["divergencias"][0]["interpretador"],
                         "python3 do sistema")
        self.assertEqual(estado["nao_provisionados"], [])
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 1)

    def test_venv_ausente_sem_fallback_e_NAO_PROVISIONADO_e_nao_reprova(self):
        """Nao ha o que divergir de um interpretador que ninguem criou.

        E o caso de `requirements-python-quality-sca.txt` e do zizmor hoje: o
        conserto e materializar o venv, e o gate imprime o comando.

        Mutacao que mata este caso: contar o venv ausente como divergencia.
        """
        self.declara("requirements-teste.txt",
                     venv_persistente="venv-que-ninguem-criou",
                     sistema="nunca",
                     materializar="./tools/python-quality-sca-env true")
        self.escreve("requirements-teste.txt", ["pip==0.0.1-inexistente"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(estado["ausencias"], [])
        self.assertEqual(len(estado["nao_provisionados"]), 1)
        item = estado["nao_provisionados"][0]
        self.assertEqual(item["venvs"], ["venv-que-ninguem-criou"])
        self.assertEqual(item["materializar"], "./tools/python-quality-sca-env true")
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 0)

    def test_symlink_do_venv_nao_faz_o_gate_medir_o_sistema(self):
        """`bin/python` de um venv e SYMLINK para o binario do sistema.

        Comparar por `os.path.realpath` iguala os dois, o curto-circuito de
        `versoes_em` dispara e o gate mede o sistema achando que mede o venv.
        Foi o que aconteceu na primeira execucao do desenho novo, em
        2026-09-10: devolveu `trafilatura 2.2.0` e `torch 2.13.0` onde os venvs
        tem 2.1.0 e 2.12.1+cpu.

        Mutacao que mata este caso: trocar `os.path.abspath` por
        `os.path.realpath` na comparacao de `versoes_em`.
        """
        venv = self.venv_com("venv-symlink", "pip", "9.9.9")
        alvo = self.raiz / venv / "bin" / "python"
        self.assertTrue(os.path.islink(alvo), "o venv nasceu sem symlink")
        self.assertEqual(os.path.realpath(alvo), os.path.realpath(sys.executable),
                         "o symlink nao aponta para o python que roda o teste")
        lidas = self.gate.versoes_em(str(alvo), ["pip"])
        self.assertEqual(lidas["pip"], "9.9.9",
                         "o gate leu o pip do SISTEMA, nao o do venv")

    def test_override_de_ambiente_vence_e_e_medido(self):
        """`WIKI_*_PYTHON` e `WIKI_*_VENV` sao o que o operador aponta a mao.

        Se o gate ignorasse o override, mediria um interpretador que ninguem
        vai usar naquela execucao.
        """
        venv = self.venv_com("venv-apontado", "pip", "9.9.9")
        self.declara("requirements-teste.txt",
                     variavel_venv="WIKI_TESTE_VENV", sistema="nunca")
        self.escreve("requirements-teste.txt", ["pip==9.9.9"])
        anterior = os.environ.get("WIKI_TESTE_VENV")
        os.environ["WIKI_TESTE_VENV"] = str(self.raiz / venv)
        try:
            estado = self.gate.confere(str(self.raiz))
        finally:
            if anterior is None:
                os.environ.pop("WIKI_TESTE_VENV", None)
            else:
                os.environ["WIKI_TESTE_VENV"] = anterior
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(estado["nao_provisionados"], [])

    def test_regime_sempre_mede_o_sistema_AINDA_QUE_o_venv_exista(self):
        """`sempre` afirma que o consumidor nunca consulta o venv.

        `internal/ptbrlexicaldiversity/lexical_diversity.go:654-657` le a
        variavel e cai direto no `python3` — o venv em `.cache/` so entra
        quando o wrapper exporta `WIKI_*_PYTHON`, e `cmd/check <nome>` chamado
        direto nao passa por ele. Logo o sistema continua vivo com o venv no
        disco, e foi exatamente por esse caminho que o nltk do sistema derivou
        para 3.10.3.

        Mutacao que mata este caso: fazer `sempre` so valer quando nao ha venv
        vivo (colapsar `sempre` em `quando_sem_venv`).
        """
        venv = self.venv_com("venv-que-o-consumidor-ignora", "pip", "9.9.9")
        self.declara("requirements-teste.txt", venv_persistente=venv,
                     sistema="sempre")
        self.escreve("requirements-teste.txt", ["pip==9.9.9"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(len(estado["divergencias"]), 1,
                         "o venv escondeu o sistema num regime `sempre`")
        self.assertEqual(estado["divergencias"][0]["interpretador"],
                         "python3 do sistema")

    def test_regime_quando_sem_venv_TIRA_o_sistema_da_conta_com_venv_vivo(self):
        """`quando_sem_venv` afirma que o consumidor consulta o venv antes.

        `internal/ossinstallmatrix/matrix.go:1952-1968` devolve o venv assim
        que ele existe e so entao chega ao `python3`. Provisionar o venv tira o
        sistema da conta; manter o vermelho depois disso seria dividia
        inventada — a mesma classe de falso vermelho que este gate corrigiu.

        Mutacao que mata este caso: fazer `quando_sem_venv` medir o sistema
        sempre (colapsar em `sempre`).
        """
        venv = self.venv_com("venv-provisionado", "pip", "9.9.9")
        self.declara("requirements-teste.txt", venv_persistente=venv,
                     sistema="quando_sem_venv")
        self.escreve("requirements-teste.txt", ["pip==9.9.9"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [],
                         "o sistema entrou na conta com o venv provisionado")
        self.assertEqual(estado["nao_provisionados"], [])

    def test_entrada_sem_regime_declarado_NAO_cai_no_sistema(self):
        """Campo ausente e desconhecido: o default seguro e `nunca`.

        Default permissivo devolveria o gate ao defeito original — medir o
        sistema por falta de declaracao, que e adivinhar.

        Mutacao que mata este caso: trocar o default de `nunca` por `sempre`.
        """
        self.mapa["tools/requirements-teste.txt"] = {
            "venv_persistente": "venv-que-ninguem-criou",
            "venv_legado": "", "variavel_venv": "", "variavel_python": "",
            "materializar": "comando de teste", "prova": "sintetico do teste",
        }
        (self.raiz / "tools" / "requirements_interpretadores.json").write_text(
            json.dumps({"arquivos": self.mapa}, ensure_ascii=False),
            encoding="utf-8")
        self.escreve("requirements-teste.txt", ["pip==0.0.1-inexistente"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["divergencias"], [],
                         "entrada sem regime caiu no python3 do sistema")
        self.assertEqual(len(estado["nao_provisionados"]), 1)

    def test_requirements_sem_entrada_no_mapa_reprova(self):
        """Arquivo novo sem interpretador declarado nao se adivinha.

        Adivinhar foi o defeito. Sem entrada o gate reprova em vez de cair no
        sistema por default — e e isso que impede o mapa de apodrecer em
        silencio quando alguem acrescentar um requirements.

        Mutacao que mata este caso: tratar entrada ausente como
        `sistema: "sempre"`.
        """
        self.escreve("requirements-orfao.txt", ["pip==0.0.1-inexistente"])
        estado = self.gate.confere(str(self.raiz))
        self.assertEqual(estado["sem_mapa"], ["tools/requirements-orfao.txt"])
        self.assertEqual(estado["divergencias"], [])
        self.assertEqual(self.gate.main(["--raiz", str(self.raiz)]), 1)


class TestMapaContraODisco(unittest.TestCase):
    """O mapa e afirmacao sobre o disco, entao o disco o confere.

    Sem estes casos o mapa vira comentario que mente — a classe de defeito que
    a R1 do contrato do dado real nomeia.
    """

    def setUp(self):
        self.mapa = json.loads(MAPA.read_text(encoding="utf-8"))["arquivos"]

    def test_todo_requirements_do_repo_tem_entrada(self):
        no_disco = {f"tools/{p.name}" for p in (RAIZ / "tools").glob("requirements-*.txt")}
        self.assertEqual(no_disco - set(self.mapa), set(),
                         "requirements sem interpretador declarado")
        self.assertEqual(set(self.mapa) - no_disco, set(),
                         "entrada do mapa apontando para requirements inexistente")

    def test_toda_prova_cita_arquivo_que_existe_na_linha_que_diz(self):
        # `jsonl` ANTES de `json`: a alternancia do `re` e da esquerda para a
        # direita, e a ordem invertida cortava
        # `trafilatura_offline_extractor_evidence.jsonl` em `.json`.
        citacao = re.compile(r"([A-Za-z0-9_./-]+\.(?:jsonl|json|go|sh|md|txt|py))(?::(\d+))?")
        conferidas = 0
        for rel, entrada in sorted(self.mapa.items()):
            prova = entrada["prova"]
            achados = citacao.findall(prova) + [
                (c, "") for c in re.findall(r"(tools/[a-z0-9-]+)(?::\d+)", prova)]
            self.assertTrue(achados, f"{rel}: prova sem arquivo citado")
            for arquivo, linha in achados:
                caminho = RAIZ / arquivo
                self.assertTrue(caminho.is_file(), f"{rel}: prova cita {arquivo}, que nao existe")
                if linha:
                    with caminho.open(encoding="utf-8", errors="replace") as aberto:
                        total = sum(1 for _ in aberto)
                    self.assertLessEqual(int(linha), total,
                                         f"{rel}: prova cita {arquivo}:{linha}, alem do fim do arquivo")
                conferidas += 1
        self.assertGreaterEqual(conferidas, len(self.mapa))

    def test_o_venv_declarado_aparece_em_algum_consumidor(self):
        """Venv renomeado no consumidor e mapa parado = gate medindo o vazio."""
        alvos = [p for p in (RAIZ / "tools").iterdir() if p.is_file()]
        alvos += list((RAIZ / "internal").rglob("*.go"))
        alvos += list((RAIZ / "cmd").rglob("*.go"))
        textos = []
        for p in alvos:
            try:
                textos.append(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
        junto = "\n".join(textos)
        for rel, entrada in sorted(self.mapa.items()):
            venv = entrada["venv_persistente"]
            if not venv:
                continue
            nome = os.path.basename(venv)
            self.assertIn(nome, junto,
                          f"{rel}: o venv {nome} nao aparece em nenhum consumidor")

    def test_fallback_declarado_casa_com_o_consumidor_que_decide(self):
        """As duas entradas que decidem o veredito de hoje, provadas no codigo.

        `oss-install-matrix` diz `quando_sem_venv` e e a unica divergencia viva;
        `ptbr-morphsyntax-oracle` diz `nunca` e e uma das quatro que eram
        falsas; `lexicalrichness` diz `sempre` e e o caminho por onde o nltk do
        sistema derivou. Se qualquer um dos tres lados do codigo mudar, este
        caso reprova antes de o gate mentir.
        """
        matrix = (RAIZ / "internal/ossinstallmatrix/matrix.go").read_text(
            encoding="utf-8", errors="replace")
        self.assertIn('return "python3"', matrix,
                      "matrix.go perdeu o fallback que o mapa declara")
        self.assertIn('".cache", "oss-python-venv"', matrix,
                      "matrix.go deixou de consultar o venv ANTES do sistema, "
                      "e e essa consulta que faz o regime ser quando_sem_venv")
        self.assertEqual(
            self.mapa["tools/requirements-oss-install-matrix.txt"]["sistema"],
            "quando_sem_venv")

        oracle = (RAIZ / "internal/ptbrmorphsyntaxoracle/oracle.go").read_text(
            encoding="utf-8", errors="replace")
        self.assertIn("nunca cai silenciosamente para o python3 do sistema", oracle,
                      "oracle.go perdeu a recusa explicita que o mapa declara")
        self.assertEqual(
            self.mapa["tools/requirements-ptbr-morphsyntax-oracle.txt"]["sistema"],
            "nunca")

        # `sempre` afirma que o consumidor cai no python3 SEM consultar venv
        # nenhum. Se alguem inserir a consulta ali, o regime passa a ser
        # quando_sem_venv e este caso reprova.
        lexical = (RAIZ / "internal/ptbrlexicaldiversity/lexical_diversity.go").read_text(
            encoding="utf-8", errors="replace")
        self.assertIn('python = "python3"', lexical)
        self.assertNotIn("lexicalrichness-venv", lexical,
                         "o oraculo passou a consultar o venv: o regime nao e "
                         "mais `sempre`")
        self.assertEqual(
            self.mapa["tools/requirements-lexicalrichness.txt"]["sistema"], "sempre")

    def test_todo_regime_declarado_e_um_dos_tres_conhecidos(self):
        """Valor fora do vocabulario cairia no default `nunca` em silencio."""
        for rel, entrada in sorted(self.mapa.items()):
            self.assertIn(entrada["sistema"], ("sempre", "quando_sem_venv", "nunca"),
                          f"{rel}: regime desconhecido no mapa")

    def test_toda_entrada_sem_fallback_diz_como_materializar(self):
        for rel, entrada in sorted(self.mapa.items()):
            if entrada["sistema"] == "sempre":
                continue
            self.assertTrue(entrada["materializar"].strip(),
                            f"{rel}: sem fallback e sem comando de materializacao, "
                            f"o vermelho nao diz o que fazer")


if __name__ == "__main__":
    unittest.main(verbosity=2)
