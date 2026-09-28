#!/usr/bin/env python3
"""Bancada de tools/cerebro-pausar.

O que esta bancada protege: que o arquivo data/ops/cerebro_pausa_manual.json
escrito pela ferramenta seja LIDO pelo daemon (internal/cerebro/pausa.go,
LePausaManual), e que o `status` diga "ilegivel" exatamente quando o daemon
diria. Um arquivo que o daemon nao le vira pausa de classe `infra` e gate
cerebro-batimento vermelho com alerta ao dono.

AS DUAS TABELAS DE ORACULO foram MEDIDAS em 2026-09-23 com go1.26.6 (o
toolchain de tools/go-modern), num programa de scratch que copia LePausaManual
linha a linha (json.Decoder + DisallowUnknownFields + time.Parse(RFC3339) +
TrimSpace). Nao sao palpite sobre o Go: sao a saida dele. Se o toolchain mudar
e o Go passar a aceitar/recusar outra coisa, a tabela e o que se re-mede.

COMO RE-MEDIR (o oraculo nao e codigo do repo; este e o programa inteiro).
Salve fora do repo como main.go e rode `GO111MODULE=off tools/go-modern run
main.go json <arquivo>` (imprime <nil> ou o erro de LePausaManual) ou sem
argumento com a lista de strings trocada, para time.Parse:

    package main
    import ("encoding/json";"fmt";"os";"strings";"time")
    type P struct {
        Motivo string `json:"motivo"`; Ate string `json:"ate"`
        DeclaradaPor string `json:"declarada_por"`; DeclaradaEm string `json:"declarada_em"`
    }
    func le(bruto string) error {
        var p P
        dec := json.NewDecoder(strings.NewReader(bruto)); dec.DisallowUnknownFields()
        if err := dec.Decode(&p); err != nil { return fmt.Errorf("ilegivel: %w", err) }
        if strings.TrimSpace(p.Ate) == "" { return fmt.Errorf("sem ate") }
        if _, err := time.Parse(time.RFC3339, p.Ate); err != nil { return fmt.Errorf("ate fora: %w", err) }
        if strings.TrimSpace(p.Motivo) == "" { return fmt.Errorf("sem motivo") }
        return nil
    }
    func main() {
        if len(os.Args) > 2 && os.Args[1] == "json" {
            b, _ := os.ReadFile(os.Args[2]); fmt.Println(le(string(b))); return
        }
        for _, s := range []string{"2026-10-07T23:59:59Z"} {
            _, err := time.Parse(time.RFC3339, s); fmt.Printf("%-36q %v\n", s, err == nil)
        }
    }

Roda como `python3 tools/test_cerebro_pausar.py` (a bancada diaria nao usa
pytest). A guarda `unittest.main()` fica no FIM, depois de todas as classes.
Cada teste usa a propria raiz temporaria via `--raiz`; o arquivo real nunca e
tocado.
"""

import datetime as dt
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

FERRAMENTA = Path(__file__).resolve().parent / "cerebro-pausar"
ARQUIVO = ("data", "ops", "cerebro_pausa_manual.json")
BATIMENTO = ("data", "ops", "cerebro_batimento.json")

FUTURO_OFFSET = "2099-10-07T23:59:59-03:00"
FUTURO_Z = "2099-10-07T23:59:59Z"
PASSADO = "2020-01-01T00:00:00Z"


def _carrega_modulo():
    sys.dont_write_bytecode = True
    loader = SourceFileLoader("cerebro_pausar_teste", str(FERRAMENTA))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    modulo = importlib.util.module_from_spec(spec)
    loader.exec_module(modulo)
    return modulo


MOD = _carrega_modulo()


# time.Parse(time.RFC3339, s) == nil, medido (ver o cabecalho).
ORACULO_RFC3339 = [
    ("2026-10-07", False),
    ("2026-10-07T23:59", False),
    ("2026-10-07T23:59:59", False),
    ("2026-10-07T23:59:59-03:00", True),
    ("2026-10-07T23:59:59Z", True),
    ("2026-10-07T23:59:59+00:00", True),
    ("2026-10-07T23:59:59.5-03:00", True),
    ("2026-10-07T23:59:59.123456789Z", True),
    ("2026-10-07T23:59:59.1234567890Z", True),
    ("2026-10-07T23:59:59,5Z", True),
    ("2026-10-07T23:59:59.Z", False),
    ("2026-10-07t23:59:59z", False),
    ("2026-10-07T23:59:59z", False),
    ("2026-10-07T23:59:59-0300", False),
    ("2026-10-07T23:59:59-03", False),
    ("2026-10-07 23:59:59-03:00", False),
    ("2026-02-30T00:00:00Z", False),
    ("2024-02-29T00:00:00Z", True),
    ("2026-10-07T24:00:00Z", False),
    ("2026-10-07T23:59:60Z", False),
    (" 2026-10-07T23:59:59Z", False),
    ("2026-10-07T23:59:59Z ", False),
    ("2026-10-07T23:59:59Z\n", False),
    ("2026-10-07T23:59:59+24:00", True),
    ("2026-10-07T23:59:59+23:60", True),
    ("2026-10-07T23:59:59+25:00", False),
    ("2026-10-07T23:59:59+23:61", False),
    ("2026-10-07T23:59:59+99:99", False),
    ("2026-10-07T23:59:59+14:00", True),
    ("2026-10-07T23:59:59-00:00", True),
    ("2026-10-07T23:59:59+0:00", False),
    ("0000-01-01T00:00:00Z", True),
    ("0000-02-29T00:00:00Z", True),
    ("0100-02-29T00:00:00Z", False),
    ("9999-12-31T23:59:59-03:00", True),
    ("0001-01-01T00:00:00+03:00", True),
    ("02026-10-07T23:59:59Z", False),
    ("2026-1-07T23:59:59Z", False),
]

_ATE = '"ate":"2026-10-07T23:59:59Z"'
# (conteudo em bytes, LePausaManual devolve erro?) -- medido (ver o cabecalho).
ORACULO_JSON = [
    ("sem declarada_por/em", b'{"motivo":"x",' + _ATE.encode() + b'}', False),
    ("chaves maiusculas", b'{"Motivo":"x","ATE":"2026-10-07T23:59:59Z"}', False),
    ("lixo depois do objeto", b'{"motivo":"x",' + _ATE.encode() + b'} lixo', False),
    ("motivo null", b'{"motivo":null,' + _ATE.encode() + b'}', True),
    ("ate numero", b'{"motivo":"x","ate":5}', True),
    ("null no topo", b'null', True),
    ("BOM", b'\xef\xbb\xbf{"motivo":"x",' + _ATE.encode() + b'}', True),
    ("vazio", b'', True),
    ("campo extra", b'{"motivo":"x",' + _ATE.encode() + b',"extra":1}', True),
    ("duplicada com null", b'{"motivo":"x",' + _ATE.encode() + b',"motivo":null}', False),
    ("dois objetos", b'{"motivo":"x",' + _ATE.encode() + b'}{"a":1}', False),
    ("array no topo", b'[]', True),
    ("declarada_por numero", b'{"motivo":"x","ate":"2026-10-07T23:59:59Z","declarada_por":5}', True),
    ("duplicada com vazio", b'{"motivo":"x",' + _ATE.encode() + b',"motivo":"  "}', True),
    ("ate com espaco", b'{"motivo":"x","ate":" 2026-10-07T23:59:59Z"}', True),
    ("newlines no fim", b'{"motivo":"x",' + _ATE.encode() + b'}\n\n', False),
    ("truncado", b'{"motivo":"x",' + _ATE.encode(), True),
    ("chave com escape", b'{"mot\\u0069vo":"x",' + _ATE.encode() + b'}', False),
    ("declarada_em objeto", b'{"motivo":"x","ate":"2026-10-07T23:59:59Z","declarada_em":{}}', True),
    ("utf8 invalido", b'{"motivo":"\xff",' + _ATE.encode() + b'}', False),
    ("K de Kelvin", b'{"motivo":"x","\xe2\x84\xaaate":"2026-10-07T23:59:59Z"}', True),
    # TrimSpace do Go (unicode.IsSpace) contra o str.strip() do Python:
    ("motivo U+001C", b'{"motivo":"\\u001c",' + _ATE.encode() + b'}', False),
    ("motivo U+001F", b'{"motivo":"\\u001f",' + _ATE.encode() + b'}', False),
    ("motivo NBSP", b'{"motivo":"\\u00a0",' + _ATE.encode() + b'}', True),
    ("motivo U+200B", b'{"motivo":"\\u200b",' + _ATE.encode() + b'}', False),
    ("motivo NEL+U+3000+U+2028", b'{"motivo":"\\u0085\\u3000\\u2028",' + _ATE.encode() + b'}', True),
    ("motivo U+180E", b'{"motivo":"\\u180e",' + _ATE.encode() + b'}', False),
    ("motivo U+FEFF", b'{"motivo":"\\ufeff",' + _ATE.encode() + b'}', False),
]


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.raiz = self._tmp.name
        self.caminho = os.path.join(self.raiz, *ARQUIVO)

    def tearDown(self):
        self._tmp.cleanup()

    def roda(self, *argv):
        return subprocess.run(
            [sys.executable, str(FERRAMENTA), *argv, "--raiz", self.raiz],
            capture_output=True, text=True, timeout=60,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def escreve_bruto(self, conteudo):
        os.makedirs(os.path.dirname(self.caminho), exist_ok=True)
        with open(self.caminho, "wb") as fh:
            fh.write(conteudo if isinstance(conteudo, bytes) else conteudo.encode("utf-8"))

    def escreve_pausa(self, **campos):
        base = {"motivo": "manutencao", "ate": FUTURO_OFFSET,
                "declarada_por": "teste", "declarada_em": "2026-09-23T06:00:00-03:00"}
        base.update(campos)
        self.escreve_bruto(json.dumps(base))

    def escreve_batimento(self, **campos):
        caminho = os.path.join(self.raiz, *BATIMENTO)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as fh:
            json.dump(campos, fh)

    def le_arquivo(self):
        with open(self.caminho, encoding="utf-8") as fh:
            return json.load(fh)


class ParidadeComOGo(unittest.TestCase):
    def test_rfc3339_igual_ao_oraculo(self):
        """Pega: regex sem re.ASCII, `$` no lugar de fullmatch (aceita "\\n"),
        esquecer a fracao com virgula, limite de offset 23:59 no leitor (o Go
        aceita 24:00), aceitar `z` minusculo, fromisoformat puro (aceita data so)."""
        divergentes = []
        for texto, go_aceita in ORACULO_RFC3339:
            try:
                MOD.analisa_rfc3339(texto)
                aceita = True
            except ValueError:
                aceita = False
            if aceita != go_aceita:
                divergentes.append((texto, go_aceita, aceita))
        self.assertEqual(divergentes, [], "divergencia (texto, go, python)")

    def test_digito_nao_ascii_recusado(self):
        """Pega: _RE_RFC3339_LEITURA sem re.ASCII -- \\d casaria digito arabe e
        int() o converteria, aceitando o que o Go recusa."""
        with self.assertRaises(ValueError):
            MOD.analisa_rfc3339("٢٠٢٦-10-07T23:59:59Z")

    def test_json_igual_ao_oraculo(self):
        """Pega: exigir as 4 chaves no leitor (o Go aceita sem declarada_por),
        casamento de chave case-sensitive, json.loads (recusa lixo depois do
        objeto que o Decoder ignora), `null` apagando valor anterior, aceitar
        numero em campo texto, fold Unicode de chave (Kelvin)."""
        divergentes = []
        for nome, conteudo, go_erra in ORACULO_JSON:
            with tempfile.TemporaryDirectory() as d:
                caminho = os.path.join(d, "p.json")
                with open(caminho, "wb") as fh:
                    fh.write(conteudo)
                try:
                    MOD.le_pausa(caminho)
                    erra = False
                except MOD.PausaIlegivel:
                    erra = True
            if erra != go_erra:
                divergentes.append((nome, go_erra, erra))
        self.assertEqual(divergentes, [], "divergencia (caso, go_erra, python_erra)")

    def test_trim_do_go_nao_e_o_strip_do_python(self):
        """Pega: trim_go trocado por str.strip() -- o Python corta U+001C, o Go
        nao, e o `status` chamaria de ilegivel um arquivo que o daemon aceita."""
        with tempfile.TemporaryDirectory() as d:
            caminho = os.path.join(d, "p.json")
            with open(caminho, "w", encoding="utf-8") as fh:
                json.dump({"motivo": "\x1c", "ate": FUTURO_Z}, fh)
            self.assertEqual(MOD.le_pausa(caminho)["motivo"], "\x1c")

    def test_ausente_e_none(self):
        """Pega: le_pausa levantando (ou devolvendo dict vazio) para arquivo
        ausente -- ausente e "sem pausa", como o `nil, nil` do Go."""
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(MOD.le_pausa(os.path.join(d, "nao-existe.json")))


class Declarar(Base):
    def test_ate_so_data_recusado(self):
        """Pega: aceitar `2026-10-07` (fromisoformat aceita) -- o Go recusa e o
        gate fica vermelho por arquivo ilegivel."""
        r = self.roda("declarar", "--motivo", "m", "--ate", "2026-10-07")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("nao e RFC3339", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_ate_sem_segundos_recusado(self):
        """Pega: regex com segundos opcionais."""
        r = self.roda("declarar", "--motivo", "m", "--ate", "2026-10-07T23:59")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("nao e RFC3339", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_ate_sem_segundos_com_fuso_recusado(self):
        """Pega: segundos opcionais na regex do ESCRITOR -- o caso acima nao
        isola a regra, porque tambem falta o fuso."""
        r = self.roda("declarar", "--motivo", "m", "--ate", "2099-10-07T23:59-03:00")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("nao e RFC3339", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_offset_absurdo_recusado_na_escrita(self):
        """Pega: escritor sem o teto -23:59..+23:59. O Go aceita +24:00, mas
        escrever isso e escrever a borda da regua; o escritor fica no subconjunto."""
        r = self.roda("declarar", "--motivo", "m", "--ate", "2099-10-07T23:59:59+24:00")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("offset fora", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_ate_sem_fuso_recusado(self):
        """Pega: fuso opcional (fromisoformat devolve datetime ingenuo e passa)."""
        r = self.roda("declarar", "--motivo", "m", "--ate", "2026-10-07T23:59:59")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("nao e RFC3339", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_ate_com_offset_aceito(self):
        """Pega: regex que so aceita `Z`. O `ate` e gravado VERBATIM."""
        r = self.roda("declarar", "--motivo", "m", "--ate", FUTURO_OFFSET)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.le_arquivo()["ate"], FUTURO_OFFSET)

    def test_ate_com_z_aceito(self):
        """Pega: regex que so aceita offset numerico."""
        r = self.roda("declarar", "--motivo", "m", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.le_arquivo()["ate"], FUTURO_Z)

    def test_motivo_vazio_recusado(self):
        """Pega: motivo so de espacos aceito -- o daemon le como ilegivel."""
        r = self.roda("declarar", "--motivo", "   ", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("--motivo vazio", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_ate_no_passado_recusado(self):
        """Pega: validar so o formato -- pausa que nasce vencida e gate
        vermelho no primeiro ciclo."""
        r = self.roda("declarar", "--motivo", "m", "--ate", PASSADO)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("ja passou", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_sobre_vigente_sem_forcar_recusa_e_preserva(self):
        """Pega: sobrescrever a pausa vigente de outra pessoa sem --forcar."""
        self.escreve_pausa(motivo="original")
        r = self.roda("declarar", "--motivo", "novo", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("renovar", r.stderr)
        self.assertEqual(self.le_arquivo()["motivo"], "original")

    def test_sobre_vigente_com_forcar_substitui(self):
        """Pega: --forcar ignorado."""
        self.escreve_pausa(motivo="original")
        r = self.roda("declarar", "--motivo", "novo", "--ate", FUTURO_Z, "--forcar")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.le_arquivo()["motivo"], "novo")

    def test_sobre_vencida_substitui_sem_forcar(self):
        """Pega: tratar pausa VENCIDA como vigente (comparacao de prazo
        invertida) -- o conserto do gate vermelho ficaria bloqueado."""
        self.escreve_pausa(motivo="velha", ate=PASSADO)
        r = self.roda("declarar", "--motivo", "nova", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("VENCIDA", r.stderr)
        self.assertEqual(self.le_arquivo()["motivo"], "nova")

    def test_escreve_exatamente_as_4_chaves_e_o_go_le(self):
        """Pega: campo a mais no arquivo (DisallowUnknownFields -> gate
        vermelho), campo faltando, declarada_em com microssegundos ou sem fuso."""
        r = self.roda("declarar", "--motivo", "m", "--ate", FUTURO_OFFSET, "--por", "quem")
        self.assertEqual(r.returncode, 0, r.stderr)
        dados = self.le_arquivo()
        self.assertEqual(list(dados), ["motivo", "ate", "declarada_por", "declarada_em"])
        self.assertEqual(dados["declarada_por"], "quem")
        self.assertIsNotNone(MOD._RE_RFC3339_ESCRITA.fullmatch(dados["declarada_em"]),
                             dados["declarada_em"])
        self.assertIsNotNone(MOD.le_pausa(self.caminho))

    def test_por_padrao_e_usuario_arroba_host(self):
        """Pega: declarada_por vazio quando --por nao e passado."""
        r = self.roda("declarar", "--motivo", "m", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("@", self.le_arquivo()["declarada_por"])

    def test_escrita_atomica_nao_deixa_temporario(self):
        """Pega: temporario esquecido no diretorio (ou escrita direta sem
        replace, que deixaria o daemon ler meio arquivo)."""
        r = self.roda("declarar", "--motivo", "m", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.caminho))),
                         ["cerebro_pausa_manual.json"])


class Renovar(Base):
    def test_sem_arquivo_recusa(self):
        """Pega: renovar criando pausa do nada (sem motivo declarado)."""
        r = self.roda("renovar", "--ate", FUTURO_Z)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("declarar", r.stderr)
        self.assertFalse(os.path.exists(self.caminho))

    def test_mantem_motivo_e_autor_troca_ate_e_data(self):
        """Pega: renovar perdendo o motivo/autor, ou nao atualizando declarada_em."""
        self.escreve_pausa(motivo="original", declarada_por="autor", ate=PASSADO)
        r = self.roda("renovar", "--ate", FUTURO_OFFSET)
        self.assertEqual(r.returncode, 0, r.stderr)
        dados = self.le_arquivo()
        self.assertEqual(dados["motivo"], "original")
        self.assertEqual(dados["declarada_por"], "autor")
        self.assertEqual(dados["ate"], FUTURO_OFFSET)
        self.assertNotEqual(dados["declarada_em"], "2026-09-23T06:00:00-03:00")
        self.assertEqual(list(dados), ["motivo", "ate", "declarada_por", "declarada_em"])

    def test_valida_ate(self):
        """Pega: renovar sem a validacao de formato do declarar."""
        self.escreve_pausa()
        r = self.roda("renovar", "--ate", "2026-10-07T23:59:59")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(self.le_arquivo()["ate"], FUTURO_OFFSET)


class Retirar(Base):
    def test_ausente_sai_zero(self):
        """Pega: retirar sem arquivo saindo com erro (ou traceback -> 2)."""
        r = self.roda("retirar")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ja nao existe", r.stdout)

    def test_presente_apaga_e_instrui(self):
        """Pega: retirar que nao apaga, ou que omite como conferir a retomada."""
        self.escreve_pausa()
        r = self.roda("retirar")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(os.path.exists(self.caminho))
        self.assertIn("tools/check-cerebro-batimento", r.stdout)


class Status(Base):
    def test_ausente(self):
        """Pega: ausencia tratada como defeito."""
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sem pausa declarada", r.stdout)

    def test_vigente(self):
        """Pega: comparacao de prazo invertida (vigente chamada de vencida)."""
        self.escreve_pausa()
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("vigente, vence em", r.stdout)
        self.assertIn("manutencao", r.stdout)

    def test_vencida_sai_1(self):
        """Pega: vencida saindo 0 -- e o estado "esqueci desligado" que o gate
        pinta de vermelho."""
        self.escreve_pausa(ate=PASSADO)
        r = self.roda("status")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("VENCIDA ha", r.stdout)

    def test_campo_extra_sai_1_e_nomeia(self):
        """Pega: leitor tolerante a campo extra (o Go usa DisallowUnknownFields)."""
        self.escreve_pausa(obs="nota")
        r = self.roda("status")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("campo desconhecido 'obs'", r.stdout)

    def test_json_quebrado_sai_1_e_nomeia(self):
        """Pega: JSON quebrado tratado como "sem pausa", ou derrubando a
        ferramenta (traceback -> 2 em vez do veredito 1)."""
        self.escreve_bruto('{"motivo": "x", "ate": ')
        r = self.roda("status")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("JSON ilegivel", r.stdout)

    def test_sem_declarada_por_e_legivel(self):
        """Pega: exigir as 4 chaves no leitor -- o Go aceita sem declarada_por
        e declarada_em, e o status gritaria onde o gate esta verde."""
        self.escreve_bruto(json.dumps({"motivo": "m", "ate": FUTURO_Z}))
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("(nao informado)", r.stdout)

    def test_batimento_que_nao_reconheceu_avisa_sem_mudar_exit(self):
        """Pega: descompasso arquivo x batimento silencioso, ou mudando o exit."""
        self.escreve_pausa()
        self.escreve_batimento(ts="2026-09-23T09:27:56Z", estado="trabalhando")
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ainda nao reconheceu", r.stdout)

    def test_batimento_que_nao_retomou_avisa(self):
        """Pega: sem arquivo e worker ainda `pausado_a_pedido` passando calado."""
        self.escreve_batimento(ts="2026-09-23T09:27:56Z", estado="pausado_a_pedido",
                               classe_pausa="manual", sonda_pausa="pausa_manual")
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ainda nao retomou", r.stdout)
        self.assertIn("pausa_manual", r.stdout)

    def test_batimento_coerente_nao_avisa(self):
        """Pega: aviso disparando sempre (falso positivo que treina a ignorar)."""
        self.escreve_pausa()
        self.escreve_batimento(ts="2026-09-23T09:40:00Z", estado="pausado_a_pedido",
                               classe_pausa="manual", sonda_pausa="pausa_manual")
        r = self.roda("status")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("AVISO", r.stdout)


if __name__ == "__main__":
    unittest.main()
