#!/usr/bin/env python3
"""Prova por MUTAÇÃO que a batida no lock de deploy mede SINAL DE VIDA, e que ela
não deixa nenhum processo capaz de sobreviver à morte do deploy.

O DEFEITO, medido em 2026-09-10
--------------------------------
`data/ops/.deploy-em-curso.lock` cala três vigias enquanto for novo e é acusado
de ÓRFÃO depois de 30 minutos, para que um deploy interrompido não desligue a
vigilância para sempre. A regra é certa. A medida não era: a idade vinha do
`mtime` de criação, e o deploy #3 levou 46 minutos — só o reaquecimento de 22.446
URLs a 12 r/s custa 31. Aos 30 minutos de um deploy VIVO, `check-http-smoke`
devolveu `http_smoke_redesocial_lock_de_deploy_orfao=47min`. Alarme falso treina
o operador a ignorar o verdadeiro, e com o acervo crescendo todo deploy futuro
cruzaria a janela.

O PERIGO DO CONSERTO ÓBVIO
---------------------------
Um processo separado tocando o lock em laço sobreviveria a `kill -9` no deploy
(o `trap` não dispara) e diria "deploy em curso" para sempre — desligando a
vigilância de vez, que é o oposto do que a detecção de órfão existe para fazer.
Por isso a batida mora no PRÓPRIO shell do script, em primeiro plano, enquanto o
comando longo roda em segundo. `test_batida_nao_sobrevive_a_morte_do_deploy`
prova isso matando o script.
"""
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# `DEPLOY_PUBLICO` existe para a PROVA POR MUTAÇÃO apontar a bancada a uma cópia
# mutada, sem sobrescrever o script vivo. É a mesma porta de
# tools/test_deploy_publico_purga_por_camada.sh.
DEPLOY = Path(os.environ.get("DEPLOY_PUBLICO", str(RAIZ / "tools/deploy-publico")))


def contem_comando(fonte, comando):
    """`comando in fonte`, indiferente ao espaço que um formatador reescreve.

    POR QUE (2026-09-16): este arquivo afirmava
    `grep -F -x -v -f "$REMOVIDOS" "$PURGE_TODOS" > "$AQUECER_LISTA"` com espaço
    depois do `>`. O shfmt colou o redirecionamento (`>"$AQUECER_LISTA"`), o
    `assertIn` passou a reprovar, e o vermelho não dizia nada sobre a subtração
    dos shards retirados — que continuava exatamente onde estava. O mesmo
    acidente matou a âncora `sed` de `tools/test_deploy_publico_purga_api.sh`,
    que extraía bloco VAZIO e reprovava com "bloco nao encontrado".

    Guarda ancorada em espaço em branco mede o formatador, não o comportamento.
    A normalização iguala runs de espaço e cola `<`, `>` e `|` aos operandos nos
    DOIS lados — o resto do comando continua literal, que é o que a asserção quer.
    """
    def aperta(texto):
        return re.sub(r"\s*([<>|])\s*", r"\1", re.sub(r"\s+", " ", texto)).strip()
    return aperta(comando) in aperta(fonte)


def conta_comando(fonte, comando):
    """Quantas vezes `comando` aparece, pela mesma normalização de espaço."""
    def aperta(texto):
        return re.sub(r"\s*([<>|])\s*", r"\1", re.sub(r"\s+", " ", texto)).strip()
    return aperta(fonte).count(aperta(comando))


def extrai_funcao():
    """Recorta do deploy o bloco da batida, para exercitá-lo sem rodar o deploy.

    Testar o trecho REAL — e não uma cópia escrita à mão neste arquivo — é o que
    faz o mutante morrer: uma cópia continuaria passando depois de alguém apagar
    a batida do deploy.
    """
    fonte = DEPLOY.read_text(encoding="utf-8")
    inicio = fonte.index('BATIDA_INTERVALO="${BATIDA_INTERVALO:-30}"')
    fim = fonte.index("\n}", inicio) + 2
    return fonte[inicio:fim]


def extrai_orcamento():
    """Recorta a função de orçamento do deploy, pelo mesmo motivo da batida:
    testar o trecho REAL, e não uma cópia que continuaria passando depois de
    alguém mudar o deploy."""
    fonte = DEPLOY.read_text(encoding="utf-8")
    # `orcamento_de_aquecimento` passou a CHAMAR `segundos_de_aquecimento` em
    # 2026-09-10, entao o recorte tem de trazer as duas — recortar so a de baixo
    # daria "command not found" e o teste mediria o proprio recorte.
    inicio = fonte.index("segundos_de_aquecimento() {")
    fim = fonte.index("\n}", fonte.index("orcamento_de_aquecimento() {")) + 2
    return fonte[inicio:fim]


class Orcamento(unittest.TestCase):
    """O orçamento do reaquecimento sai da LISTA, não de uma constante.

    O `timeout 1800` fixo estourou por 68 segundos no deploy #4: 22.414 URLs a
    12 r/s custam 1.868 s. Não era carga — era aritmética, e ia estourar em todo
    deploy que trocasse binário, cada vez mais cedo conforme o acervo cresce.
    """

    def estima(self, urls):
        return self.roda("segundos_de_aquecimento %d" % urls)

    def roda(self, chamada):
        script = ("#!/usr/bin/env bash\nset -u\n" + extrai_orcamento()
                  + "\n" + chamada + "\n")
        concluido = subprocess.run(["bash", "-c", script], capture_output=True,
                                   text=True, timeout=60)
        self.assertEqual(concluido.returncode, 0, concluido.stderr)
        return int(concluido.stdout.strip())

    def calcula(self, urls):
        script = ("#!/usr/bin/env bash\nset -u\n" + extrai_orcamento()
                  + "\norcamento_de_aquecimento %d\n" % urls)
        concluido = subprocess.run(["bash", "-c", script], capture_output=True,
                                   text=True, timeout=60)
        self.assertEqual(concluido.returncode, 0, concluido.stderr)
        return int(concluido.stdout.strip())

    def test_a_lista_do_deploy_4_cabe_com_folga(self):
        """22.414 URLs custam 1.868 s reais; o orçamento tem de cobrir isso."""
        orcamento = self.calcula(22414)
        self.assertGreater(orcamento, 22414 / 12,
                           "o orcamento tem de ser maior que o tempo teorico")
        self.assertEqual(orcamento, 2988)

    def test_lista_curta_ganha_o_piso(self):
        """Uma lista de 12 URLs não pode morrer num timeout de 1 segundo."""
        self.assertEqual(self.calcula(12), 300)

    def test_lista_que_nao_cabe_devolve_zero_e_nao_o_teto(self):
        """Acima do teto a resposta certa NÃO é um número menor: é dizer que não
        cabe. Cortar em 3600 gastaria a hora inteira segurando o lock pesado para
        imprimir o mesmo aviso no fim."""
        self.assertEqual(self.calcula(60000), 0)

    def test_a_fronteira_do_teto(self):
        """27.000 URLs dão exatamente 3.600 s e ainda cabem; uma a mais não."""
        self.assertEqual(self.calcula(27000), 3600)
        self.assertEqual(self.calcula(27008), 0)

    def test_a_mensagem_do_delegado_le_a_MESMA_funcao_que_decide(self):
        """O numero impresso e o numero que decide — nao uma formula paralela.

        Ate 2026-09-10 a linha do reaquecimento delegado saia assim:

            27165 URLs a 12 r/s levariam 2263s, acima do teto de 3600s

        2.263 nao e acima de 3.600, e a frase se contradizia sozinha na tela.
        A mensagem imprimia `$(( TODOS_N / 12 ))` — a lista de PURGA, sem a
        folga de 1,6x — enquanto a decisao usava
        `orcamento_de_aquecimento "$AQUECER_N"`, que e a lista de AQUECIMENTO
        COM a folga. Duas variaveis e duas formulas para a mesma pergunta.
        """
        fonte = DEPLOY.read_text(encoding="utf-8")
        delegado = [l for l in fonte.splitlines() if "DELEGADO ao timer" in l]
        self.assertEqual(len(delegado), 1, "a linha do delegado deixou de ser unica")
        linha = delegado[0]
        self.assertIn('segundos_de_aquecimento "$AQUECER_N"', linha)
        self.assertNotIn("TODOS_N / 12", linha)
        self.assertNotIn("$TODOS_N URLs", linha)

    def test_a_estimativa_impressa_bate_com_a_decisao(self):
        """Nos dois lados da fronteira: o numero da mensagem explica o veredito.

        27.165 e o caso real do deploy de 2026-09-10 — 3.622 s, que estoura o
        teto por 0,6%. 22.361 e o do ciclo #6, que coube e rodou.
        """
        for urls, estimado, orcado in ((27165, 3622, 0), (22361, 2981, 2981)):
            self.assertEqual(self.estima(urls), estimado)
            self.assertEqual(self.calcula(urls), orcado)
            if orcado == 0:
                self.assertGreater(self.estima(urls), 3600,
                                   "delegou, entao a estimativa TEM de passar do teto")
            else:
                self.assertLessEqual(self.estima(urls), 3600)

    def test_a_folga_de_16_esta_na_estimativa_e_nao_so_na_decisao(self):
        """Sem a folga, 27.165 dariam 2.263 s e a mensagem voltaria a mentir."""
        self.assertEqual(self.estima(27165), 27165 * 16 // 10 // 12)
        self.assertNotEqual(self.estima(27165), 27165 // 12)

    def test_o_deploy_usa_a_funcao_e_nao_um_numero(self):
        """A fonte do argumento mudou de `$TODOS_N` para `$AQUECER_N` em
        2026-09-10, quando os shards retirados sairam da lista de aquecimento: o
        orcamento tem de sair da lista que sera AQUECIDA, nao da que foi purgada.
        `ListaDeAquecimento.test_o_orcamento_sai_da_lista_de_aquecimento_e_nao_da_de_purga`
        guarda esse lado; aqui fica o que nao muda — a funcao, nunca a
        constante."""
        fonte = DEPLOY.read_text(encoding="utf-8")
        self.assertIn("DIRIGIDO_ORCAMENTO=$(orcamento_de_aquecimento ", fonte)
        self.assertNotIn("timeout 1800 tools/warm-edge-cache", fonte)
        self.assertNotIn("DIRIGIDO_ORCAMENTO=1800", fonte)


class ListaDeAquecimento(unittest.TestCase):
    """O que foi RETIRADO entra na purga e sai do aquecimento.

    `check-sitemap-shard-grace --listar-removidos` entra na lista de purga de
    propósito: shard retirado ao fim da carência some do disco e a borda seguiria
    servindo a cópia 200 dele por até sete dias. Aquecer é o oposto — a origem
    responde 410, e 410 nunca esquenta.

    Medido no deploy #5 de 2026-09-10: `aquecidas: 22392 em 1866s`,
    `status: {200: 22364, 410: 28}` — as 28 falhas eram exatamente os shards que
    o próprio script tinha removido. Como `warm-edge-cache` sai com código de
    erro em qualquer falha, o deploy anunciou "não concluiu em 2985s" sobre uma
    passada que terminou em 63% do orçamento.
    """

    def test_o_deploy_subtrai_os_removidos_da_lista_de_aquecimento(self):
        fonte = DEPLOY.read_text(encoding="utf-8")
        self.assertTrue(
            contem_comando(fonte, 'grep -F -x -v -f "$REMOVIDOS" "$PURGE_TODOS" > "$AQUECER_LISTA"'),
            "o deploy tem de subtrair os removidos da lista de aquecimento")
        self.assertTrue(contem_comando(fonte, 'tools/warm-edge-cache --de-arquivo "$AQUECER_LISTA"'))
        # E a purga continua levando os removidos: é para isso que eles entram.
        #
        # SÃO DUAS OCORRÊNCIAS, e contá-las importa — o deploy tem dois caminhos
        # (nenhuma página mudou × alguma mudou) e cada um monta a própria lista
        # de purga. Um `assertIn` casaria a segunda e deixaria passar a remoção
        # da primeira: foi exatamente o que um mutante provou em 2026-09-10,
        # sobrevivendo à asserção fraca.
        self.assertEqual(
            conta_comando(fonte, 'tools/check-sitemap-shard-grace --listar-removidos >> "$PURGE_TODOS"'), 2,
            "os dois caminhos de purga têm de levar os shards retirados")
        self.assertTrue(contem_comando(fonte, 'tools/purge-edge-cache --de-arquivo "$PURGE_TODOS"'))

    def test_o_orcamento_sai_da_lista_de_aquecimento_e_nao_da_de_purga(self):
        fonte = DEPLOY.read_text(encoding="utf-8")
        self.assertTrue(contem_comando(fonte, 'DIRIGIDO_ORCAMENTO=$(orcamento_de_aquecimento "$AQUECER_N")'))
        self.assertFalse(contem_comando(fonte, 'orcamento_de_aquecimento "$TODOS_N"'))

    def test_a_subtracao_funciona(self):
        """`grep -F -x -v -f` tira linha inteira e literal — sem casar prefixo."""
        diretorio = tempfile.mkdtemp()
        purga = Path(diretorio) / "purga.txt"
        removidos = Path(diretorio) / "removidos.txt"
        purga.write_text("https://x/a/\nhttps://x/sitemaps/pages-0003.xml\n"
                         "https://x/b/\nhttps://x/sitemaps/pages-0004.xml\n", encoding="utf-8")
        removidos.write_text("https://x/sitemaps/pages-0003.xml\n"
                             "https://x/sitemaps/pages-0004.xml\n", encoding="utf-8")
        concluido = subprocess.run(
            ["bash", "-c", 'grep -F -x -v -f "%s" "%s"' % (removidos, purga)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(concluido.stdout.split(), ["https://x/a/", "https://x/b/"])

    def test_o_aviso_distingue_estouro_de_falha(self):
        """Tratar `timeout` (124) e erro do aquecedor como a mesma coisa foi o que
        fez o #5 anunciar estouro de orçamento numa passada concluída."""
        fonte = DEPLOY.read_text(encoding="utf-8")
        self.assertTrue(contem_comando(fonte, 'if [ "$AQUECER_RC" -eq 124 ]; then'))
        self.assertIn("ESTOUROU o orcamento", fonte)
        self.assertIn("CONCLUIU com falhas", fonte)


class Batida(unittest.TestCase):
    def monta(self, corpo):
        """Escreve um script que declara o lock, importa a batida real e roda
        `corpo`."""
        diretorio = tempfile.mkdtemp()
        lock = Path(diretorio) / "deploy.lock"
        lock.write_text("", encoding="utf-8")
        script = Path(diretorio) / "roda.sh"
        script.write_text(
            "#!/usr/bin/env bash\nset -u\n"
            'DEPLOY_LOCK="%s"\n' % lock
            + extrai_funcao() + "\n" + corpo + "\n",
            encoding="utf-8")
        script.chmod(0o755)
        return lock, script

    def test_a_funcao_existe_no_deploy(self):
        self.assertIn("com_batida_no_lock", DEPLOY.read_text(encoding="utf-8"))

    def test_o_lock_e_tocado_enquanto_o_comando_vive(self):
        lock, script = self.monta('BATIDA_INTERVALO=1 com_batida_no_lock sleep 3')
        antes = lock.stat().st_mtime
        time.sleep(0.05)
        concluido = subprocess.run(["bash", str(script)], capture_output=True,
                                   text=True, timeout=60)
        self.assertEqual(concluido.returncode, 0, concluido.stderr)
        self.assertGreater(lock.stat().st_mtime, antes,
                           "o lock tinha de ter sido tocado durante os 3s")

    def test_o_codigo_de_saida_do_comando_e_preservado(self):
        """A batida não pode engolir a falha do comando que ela acompanha —
        deploy que 'passa' porque o envelope comeu o exit é a armadilha que este
        repositório já registrou em `shell-exit-code-pipelines`."""
        _, script = self.monta('BATIDA_INTERVALO=1 com_batida_no_lock bash -c "exit 7"; echo "codigo=$?"')
        concluido = subprocess.run(["bash", str(script)], capture_output=True,
                                   text=True, timeout=60)
        self.assertIn("codigo=7", concluido.stdout)

    def test_a_saida_do_comando_continua_visivel(self):
        _, script = self.monta('BATIDA_INTERVALO=1 com_batida_no_lock echo "linha do comando"')
        concluido = subprocess.run(["bash", str(script)], capture_output=True,
                                   text=True, timeout=60)
        self.assertIn("linha do comando", concluido.stdout)

    def test_batida_nao_sobrevive_a_morte_do_deploy(self):
        """A prova que separa este conserto do conserto errado: com o script
        morto, o lock TEM de parar de ser tocado, para que a detecção de órfão
        volte a funcionar."""
        lock, script = self.monta(
            'BATIDA_INTERVALO=1 com_batida_no_lock bash -c \'echo $$ > "%s"; exec sleep 60\''
            % (Path(tempfile.gettempdir()) / "batida-filho.pid"))
        arquivo_do_filho = Path(tempfile.gettempdir()) / "batida-filho.pid"
        if arquivo_do_filho.exists():
            arquivo_do_filho.unlink()
        # `start_new_session` põe o script no PRÓPRIO grupo de processos, para que
        # o encerramento alcance só o que este teste criou. Nunca `pkill -f`: ele
        # casa por linha de comando e já matou processo de outra sessão nesta
        # máquina — é proibição escrita do contrato.
        processo = subprocess.Popen(["bash", str(script)], start_new_session=True,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2.5)
        tocado_com_o_deploy_vivo = lock.stat().st_mtime
        os.killpg(os.getpgid(processo.pid), signal.SIGKILL)
        processo.wait(timeout=10)
        time.sleep(3)
        self.assertEqual(lock.stat().st_mtime, tocado_com_o_deploy_vivo,
                         "algo continuou tocando o lock depois de o deploy morrer")

    def test_os_tres_comandos_longos_do_deploy_batem(self):
        """Reaquecimento de borda (2 pontos) e de origem: são os passos que
        cruzam a janela de 30 min. Se alguém acrescentar um quarto passo longo
        sem batida, este teste não o pega — mas os três medidos ficam presos.

        O alvo do reaquecimento dirigido deixou de ser `timeout 1800` em
        2026-09-10: o orçamento passou a sair da lista (`$DIRIGIDO_ORCAMENTO`),
        e este teste seguiu a mudança em vez de ser afrouxado — continua exigindo
        a batida no comando exato que o deploy roda."""
        fonte = DEPLOY.read_text(encoding="utf-8")
        for alvo in ("com_batida_no_lock tools/warm-origin-cache",
                     "com_batida_no_lock timeout \"$AQUECER_ORCAMENTO\" tools/warm-edge-cache",
                     "com_batida_no_lock timeout \"$DIRIGIDO_ORCAMENTO\" tools/warm-edge-cache --de-arquivo"):
            self.assertIn(alvo, fonte, "sem batida: " + alvo)

    def test_nao_ha_processo_de_batida_em_segundo_plano(self):
        """A batida em `&` seria o conserto errado. O laço tem de estar em
        primeiro plano, e só o COMANDO em segundo."""
        funcao = extrai_funcao()
        corpo = funcao[funcao.index("com_batida_no_lock()"):]
        linhas_em_background = [l for l in corpo.splitlines()
                                if l.rstrip().endswith("&") and '"$@"' not in l]
        self.assertEqual(linhas_em_background, [],
                         "só o comando acompanhado pode ir para segundo plano")


if __name__ == "__main__":
    unittest.main()
