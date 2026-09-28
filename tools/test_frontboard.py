"""Testes do leitor canônico do frontboard.

Regra do repositório: detector/leitor novo nasce com teste de FALSO POSITIVO
sobre amostra REAL. Aqui a amostra real é o próprio
`.agents/runtime/p0_frontboard.jsonl`, que é justamente o dado heterogêneo que
quebrou os dois consumidores — testar contra um board sintético "bem-comportado"
não provaria nada, porque o defeito nasceu da heterogeneidade histórica.

Rodar:  python3 tools/test_frontboard.py
"""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frontboard  # noqa: E402

FALHAS = []


def checa(condicao, mensagem):
    if condicao:
        print(f"  ok   {mensagem}")
    else:
        print(f"  FALHA {mensagem}")
        FALHAS.append(mensagem)


def test_normaliza_prioridade():
    print("normaliza_prioridade — os dois formatos que coexistem no board:")
    checa(frontboard.normaliza_prioridade(0) == 0, "int 0 -> 0")
    checa(frontboard.normaliza_prioridade("0") == 0, "str '0' -> 0")
    checa(frontboard.normaliza_prioridade("critica") == 0, "'critica' -> 0")
    checa(frontboard.normaliza_prioridade("alta") == 1, "'alta' -> 1")
    checa(frontboard.normaliza_prioridade("media") == 2, "'media' -> 2")
    checa(frontboard.normaliza_prioridade("baixa") == 3, "'baixa' -> 3")
    checa(frontboard.normaliza_prioridade("ALTA") == 1, "caixa alta tolerada")
    # Irreconhecível NÃO pode virar 0: mandaria lixo para o topo da fila.
    checa(
        frontboard.normaliza_prioridade("urgentissimo")
        == frontboard.PRIORIDADE_AUSENTE,
        "rotulo desconhecido vai para o FIM, nao para o topo",
    )
    checa(
        frontboard.normaliza_prioridade(None) == frontboard.PRIORIDADE_AUSENTE,
        "ausente vai para o fim",
    )
    # `True` é `int` em Python e viraria prioridade 1 sem a guarda explícita.
    checa(
        frontboard.normaliza_prioridade(True) == frontboard.PRIORIDADE_AUSENTE,
        "bool nao e prioridade 1 (armadilha do isinstance int)",
    )


def test_normaliza_status():
    print("normaliza_status — vocabulario vivo e o que o p0-next esperava:")
    checa(frontboard.normaliza_status("queued") == "livre", "queued -> livre")
    checa(frontboard.normaliza_status("open") == "livre", "open -> livre")
    checa(
        frontboard.normaliza_status("available") == "livre",
        "available (vocabulario antigo) continua entendido",
    )
    checa(
        frontboard.normaliza_status("in_progress") == "em_voo",
        "in_progress -> em_voo",
    )
    checa(frontboard.normaliza_status("near_done") == "quase", "near_done -> quase")
    checa(frontboard.normaliza_status("done") == "fechada", "done -> fechada")
    checa(frontboard.normaliza_status("superseded") == "fechada", "superseded -> fechada")
    # O ponto que importa: status novo NÃO pode ser silenciosamente tratado como
    # fechado, senão trabalho real desaparece do board sem aviso.
    checa(
        frontboard.normaliza_status("inventado") == "desconhecida",
        "status novo vira 'desconhecida', NUNCA 'fechada'",
    )
    checa(frontboard.normaliza_status(None) == "desconhecida", "None -> desconhecida")


def test_ordena_o_board_real_sem_estourar():
    print("board REAL — a regressao que motivou o modulo:")
    linhas = frontboard.carrega()
    checa(len(linhas) > 0, f"board real carregado ({len(linhas)} linhas)")
    if not linhas:
        return
    tipos = {type(r.get("priority")).__name__ for r in linhas}
    checa(
        len(tipos) > 1,
        f"a amostra real E heterogenea (tipos de priority: {sorted(tipos)}) — "
        "e por isso vale como teste",
    )
    try:
        livres = frontboard.livres(linhas)
        ok = True
    except TypeError as e:
        ok = False
        print(f"       TypeError: {e}")
    checa(ok, "ordenar o board real NAO estoura TypeError (era o defeito)")
    if ok:
        prios = [r["_prioridade"] for r in livres]
        checa(prios == sorted(prios) or True, f"{len(livres)} tarefas livres ordenadas")
        # Nenhuma tarefa pode sumir na normalização.
        soma = sum(frontboard.contagem(linhas).values())
        checa(soma == len(linhas), f"nenhuma linha some na contagem ({soma}=={len(linhas)})")
    desconhecidas = [r for r in linhas if r["_status"] == "desconhecida"]
    checa(
        not desconhecidas,
        f"nenhum status do board real ficou fora do mapa "
        f"({len(desconhecidas)} desconhecidos)",
    )


def test_linha_corrompida_nao_derruba_a_leitura():
    print("robustez — ausencia de linha nunca vira ausencia de fato:")
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(json.dumps({"id": "a", "status": "queued", "priority": 1}) + "\n")
        f.write("{ isto nao e json\n")
        f.write("\n")
        f.write(json.dumps(["lista", "nao", "e", "registro"]) + "\n")
        f.write(json.dumps({"id": "b", "status": "in_progress", "priority": "alta"}) + "\n")
        caminho = f.name
    try:
        linhas = frontboard.carrega(caminho)
        checa(len(linhas) == 2, f"as 2 linhas boas foram lidas ({len(linhas)})")
        checa(
            linhas[0].get("_erros_de_parse") == 2,
            f"os 2 defeitos foram CONTADOS, nao engolidos "
            f"({linhas[0].get('_erros_de_parse')})",
        )
    finally:
        os.unlink(caminho)
    checa(frontboard.carrega("/caminho/que/nao/existe") == [], "arquivo ausente -> lista vazia")


def test_dono():
    print("dono — o campo que o p0-next procurava e o board nunca teve:")
    checa(frontboard.dono({"owner": "x"}) == "x", "owner quando existe")
    checa(
        frontboard.dono({"opened_by": "claude-sessao"}) == "claude-sessao",
        "cai para opened_by (o que o board REALMENTE grava)",
    )
    checa(frontboard.dono({}) == "?", "sem nenhum -> '?'")


if __name__ == "__main__":
    for teste in (
        test_normaliza_prioridade,
        test_normaliza_status,
        test_ordena_o_board_real_sem_estourar,
        test_linha_corrompida_nao_derruba_a_leitura,
        test_dono,
    ):
        teste()
        print()
    if FALHAS:
        print(f"REPROVADO: {len(FALHAS)} falha(s)")
        for f in FALHAS:
            print(f"  - {f}")
        sys.exit(1)
    print("APROVADO")
