"""saida_de_medidor — um instrumento que CAI nao pode entregar o numero de quem MEDIU.

Este modulo existe por um defeito estrutural medido em 2026-09-16, e o defeito
nao estava em nenhuma ferramenta: estava na juncao entre o rodape delas e a
convencao de exit code das units.

────────────────────────────────────────────────────────────────────────────
A CONVENCAO QUE ESTE REPOSITORIO USA, e que continua valendo

    exit 0   MEDIU, e esta sao
    exit 1   MEDIU, e esta degradado  -> VEREDITO. A unit mascara de proposito
             (`SuccessExitStatus=0 1`), porque alertar em veredito de rotina
             treina o dono a ignorar o canal.
    exit >=2 NAO MEDIU, ou o processo quebrou -> DEFEITO DE PROCESSO. A unit
             NAO mascara, entra em `failed`, e o `OnFailure` avisa o dono.

Ela esta escrita em tools/run-daily-content:264-278 e em
ops/systemd/wikijuridica-daily-content.service:52-55, e e DELIBERADA. A mascara
do 1 e justamente o que preserva o alarme do 2.

────────────────────────────────────────────────────────────────────────────
O BURACO: TODA EXCECAO NAO TRATADA VIRA 1

Toda ferramenta Python de tools/ terminava em `sys.exit(main())`. O interpretador
sai com 1 quando uma excecao sobe ate o topo. Entao:

    traceback  =>  exit 1  =>  a unit mascara  =>  Result=success  =>  OnFailure MUDO

O resultado e a pior classe de falha que existe neste projeto: o instrumento
quebrado e indistinguivel do instrumento que mediu e disse "esta tudo bem". Um
`requests.ConnectionError` no meio da sonda, um `KeyError` num JSON que mudou de
forma, um `PermissionError` num ledger — todos entregavam o numero de quem
mediu, e ninguem era avisado.

E vale INCLUSIVE para as ferramentas que ja distinguem 1 de 2 no codigo, porque
o `return 2` delas so cobre o erro ANTECIPADO. Excecao nao tratada e, por
definicao, a que ninguem antecipou.

────────────────────────────────────────────────────────────────────────────
O QUE ESTE HELPER FAZ, e por que e um helper e nao 19 edicoes

Trocar `sys.exit(main())` por `main_protegido(main)` e uma linha por ferramenta.
Escrever o try/except em cada uma seria 19 copias da mesma logica, e a vigesima
nasceria sem ela. O comportamento fica num lugar so, com um teste ao lado
(tools/test_saida_de_medidor.py).

  - excecao nao tratada  -> imprime o traceback COMPLETO (o diagnostico nao se
                           perde: quem for consertar precisa dele) e a frase
                           `NAO MEDIDO:` no stderr, e sai com 2.
  - KeyboardInterrupt    -> 130, a convencao do shell para SIGINT. Nao e defeito
                           do instrumento: foi um operador que desistiu.
  - SystemExit           -> PROPAGA intacto. E o que `argparse` levanta ao
                           recusar uma flag (com codigo 2, que ja e o certo) e o
                           que um `sys.exit(...)` deliberado dentro do main usa.
                           Reescrever esse codigo seria apagar a decisao de quem
                           o escreveu.
  - retorno normal       -> sai com o codigo que o main devolveu, sem tocar.

POR QUE `BaseException` E NAO `Exception`: `MemoryError` e o proprio SIGINT
herdam de BaseException, e "o processo ficou sem memoria no meio da sonda" e
exatamente um "NAO MEDI". Capturar so `Exception` deixaria a classe mais grave
escapar de volta para o exit 1. SystemExit e KeyboardInterrupt vem ANTES na
cadeia de except justamente para nao serem engolidos por ela.

ISTO NAO E MASCARAR ERRO — e o oposto. O traceback continua inteiro no stderr e
no journal; o que muda e so o numero, que passa a dizer a verdade sobre o que
aconteceu. Mascarar seria o `except: pass` que este repositorio proibe.
"""

import sys
import traceback

# Os tres codigos sao constantes nomeadas para que o teste e o gate
# check-units-alarme falem deles pelo nome, e nao por literal espalhado.
CODIGO_NAO_MEDIDO = 2
CODIGO_INTERROMPIDO = 130

# A frase e ANCORA LITERAL: tools/check-units-alarme procura por ela para provar
# que a ferramenta chamada por uma unit que mascara exit 1 tem a protecao. Mudar
# o texto sem mudar o gate quebra a deteccao em silencio.
PREFIXO_NAO_MEDIDO = "NAO MEDIDO:"


def main_protegido(main, *args, **kwargs):
    """Executa `main` e traduz queda em exit 2. Nunca retorna: sempre sai."""
    try:
        codigo = main(*args, **kwargs)
    except SystemExit:
        # Decisao deliberada de quem escreveu o main (inclusive o exit 2 que o
        # argparse ja usa para invocacao invalida). Propaga sem reescrever.
        raise
    except KeyboardInterrupt:
        print(
            "%s interrompido por sinal do operador (SIGINT) — nenhum veredito foi "
            "produzido." % PREFIXO_NAO_MEDIDO,
            file=sys.stderr,
        )
        sys.exit(CODIGO_INTERROMPIDO)
    except BaseException:
        traceback.print_exc()
        print(
            "%s a ferramenta caiu antes de concluir a medicao. O traceback acima e o\n"
            "  defeito a corrigir. Este processo sai com %d (DEFEITO DE PROCESSO) e nao\n"
            "  com 1, porque 1 e o codigo de quem MEDIU e encontrou degradacao — e a\n"
            "  unit mascara o 1. Sair com 1 aqui esconderia a queda atras de\n"
            "  `Result=success` e o OnFailure nunca dispararia."
            % (PREFIXO_NAO_MEDIDO, CODIGO_NAO_MEDIDO),
            file=sys.stderr,
        )
        sys.exit(CODIGO_NAO_MEDIDO)
    sys.exit(codigo)
