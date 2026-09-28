"""accessledger — o ledger de acesso do processo Go, lido sem contar tráfego forjado.

POR QUE UM MÓDULO, E NÃO UM FILTRO DENTRO DE CADA LEITOR: em 2026-08-12 o
harness de smoke do `cmd/check` (checkGooglebotSmoke → runHTTPSmokeExpectations)
instanciou o handler HTTP de PRODUÇÃO — middleware de log incluído — e varreu o
`published_manifest` inteiro com dois User-Agents de Googlebot. Cada visita virou
uma linha em `data/ops/access/access-2026-08-12.jsonl` com
`bot_simulation:false`, `warming:false` e `bot_class:"valuable_search_or_user_bot"`.

O filtro que existia (`tools/check-bot-traffic`, `load()`) descarta linha com
`warming` ou `bot_simulation` verdadeiros. Como o harness não mandava o header,
os dois campos saíram `false` e as 19.253 requisições sintéticas passaram pelo
filtro criado exatamente para barrá-las: o relatório passou a dizer
"Googlebot: 19.259" num dia em que a borda da Cloudflare viu Googlebot real na
ordem de dezenas. Inflar métrica de bot é tratado como fraude pelo contrato do
projeto (CLAUDE.md, "ZERO FAKE").

O harness já foi corrigido (`internal/checks/checks.go`, `httpSimulationHeader`,
commit 4e997e6e): toda requisição sintética do pacote passa a mandar
`X-Bot-Simulation: true`. Isso protege o FUTURO. As linhas já gravadas continuam
mentindo, e o ledger é append-only — apagar linha, reescrever arquivo ou reverter
estado é proibido pelo repositório. A saída honesta é a mesma que a borda já
usou em `tools/edgetelemetry.py`: a linha ruim FICA onde está, visível e
auditável, e um ledger paralelo registra, com motivo e revisor, que ela não entra
em nenhuma conta.

O critério mora aqui, num lugar só, porque quem lê o access log vai crescer. Se
cada leitor tivesse o próprio filtro, um deles voltaria a somar a varredura.

────────────────────────────────────────────────────────────────────────────
COMO OS TETOS FORAM MEDIDOS (não são constante mágica)

Corpus: as 42.475 linhas dos 7 arquivos `data/ops/access/access-*.jsonl`
(2026-08-06 a 2026-08-12), agrupadas em SESSÕES — sequências do mesmo
User-Agent, no mesmo arquivo, com intervalo <= 60 s entre requisições
consecutivas —, contando só linha com `warming:false` e `bot_simulation:false`
(o que já é declaradamente sintético não precisa de detector).

  SESSÕES REAIS (as 3 varreduras do harness excluídas à mão)
    • maior sessão                     :   297 linhas (razão de varredura 0,42)
    • maior taxa com >= 100 linhas     :   4,8 requisições/s
    • maior taxa em qualquer sessão    :  31,0 req/s — mas com 31 linhas só
    • maior cobertura do acervo        :  ~125 URLs distintas = 1,3% de 9.835

  SESSÕES DO HARNESS (as 3 varreduras)
    •  9.627 linhas | 196,5 req/s | razão 1,00 | Googlebot mobile   | 06:32
    •  9.626 linhas | 196,4 req/s | razão 1,00 | Googlebot desktop  | 06:32
    •  9.638 linhas | 214,2 req/s | razão 1,00 | User-Agent vazio   | 06:34-35

Entre o teto real (297 linhas / 4,8 req/s) e o piso do harness (9.626 linhas /
196 req/s) há mais de uma ordem de grandeza de folga nos dois eixos. Os limiares
abaixo ficam no meio dessa folga.

ATENÇÃO AO FALSO POSITIVO — este detector nasce com teste sobre amostra real
(`tools/test_accessledger.py`), como manda a regra do repositório. O critério
ingênuo que primeiro se pensa ("muita requisição do mesmo agente") acusaria o
watchdog interno, que faz ~1.400 requisições por dia; ele passa por dois
motivos, e os dois importam: vem com `warming:true` e repete as mesmas 4 rotas,
então a razão de varredura fica perto de zero. Um flood na MESMA URL também não
é varredura — é outro defeito, com dono próprio — e por isso a razão de
varredura entra como condição, não como enfeite.
"""
import datetime
import json
import os
import sys
import os as _os
import glob as _glob
import json as _json
import datetime as _dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edgetelemetry  # noqa: E402  (tools/ nao e pacote; o caminho entra acima)

# Intervalo máximo entre duas requisições do mesmo agente para que continuem na
# MESMA sessão. 60 s é generoso de propósito: uma varredura estrangulada (o
# harness rodando devagar numa máquina carregada) continua sendo uma sessão só,
# em vez de virar dezenas de rajadas pequenas que escapam de qualquer teto.
JANELA_SESSAO_S = 60

# Piso de linhas para uma sessão ser candidata a varredura sintética.
# Maior sessão REAL medida: 297. 1.000 dá 3,4x de folga sobre ela e fica 9,6x
# abaixo da menor varredura do harness (9.626).
MIN_LINHAS_RAJADA = 1000

# Piso de taxa. Maior taxa REAL com volume relevante (>= 100 linhas): 4,8 req/s.
# 20 dá 4x de folga sobre isso e fica ~10x abaixo dos 196 req/s do harness.
# Sessão curta e rápida (31 req/s em 31 linhas, do wikijuridica-check) não cai
# aqui porque o piso de LINHAS também precisa ser vencido.
MIN_TAXA_RAJADA_RPS = 20.0

# Razão de varredura = URLs distintas / linhas da sessão. Uma varredura de
# acervo visita cada URL uma vez (razão ~1,00); tráfego real bate repetidas
# vezes nas mesmas rotas (as sessões reais grandes ficam entre 0,15 e 0,50).
# Esta condição é o que separa "varredura sintética" de "flood na mesma URL",
# que é defeito de outra natureza e não deve ser silenciado como sintético.
MIN_RAZAO_VARREDURA = 0.95

# Gatilho alternativo, para a varredura LENTA: qualquer sessão que cubra metade
# do acervo público é sintética por construção. Desde o cutover de 2026-08-06 o
# nginx serve as páginas do acervo direto do disco (`try_files` em
# ops/nginx/wikijuridica.conf), e só o que cai no fallback chega ao processo Go —
# um crawler externo não tem como enumerar o acervo inteiro NESTE log. Maior
# cobertura real medida: 1,3%.
MIN_COBERTURA_ACERVO = 0.5

# Terceiro gatilho, e o unico que nao depende de VOLUME: rota que o ingress
# publico nunca entrega. O nginx responde 404 em `/metrics` antes de encostar no
# Go (`location = /metrics { return 404; }`, ops/nginx/wikijuridica.conf:384),
# entao NAO EXISTE cliente externo capaz de arrancar um 200 dessa rota. Uma
# linha assim no access log so pode ter nascido DENTRO do processo — harness que
# instancia o handler de producao e fala com ele em memoria.
#
# POR QUE PRECISOU EXISTIR (auditoria de 2026-08-12): os dois gatilhos acima sao
# estatisticos e pedem rajada (>=1.000 linhas) ou cobertura (>=50% do acervo).
# O produtor achado nesta rodada emite TRES linhas por execucao — `/` com UA de
# Googlebot, `/` com UA de Chrome e `/metrics` — e passava verde por ser pequeno
# demais para qualquer limiar de volume. Detector que so enxerga contaminacao
# grande deixa passar a pequena, que e justamente a que ninguem confere.
#
# O criterio e categorico, nao estatistico: nao ha teto a calibrar nem falso
# positivo possivel enquanto o ingress bloquear a rota. Se um dia `/metrics` for
# exposto publicamente, esta constante tem que sair junto — e o teste que
# acompanha o check falha primeiro, de proposito.
ROTAS_BLOQUEADAS_NO_INGRESS = {"/metrics"}

SCHEMA = "access_ledger_quarantine_v1"

# Campos que definem a identidade de uma linha para efeito de exclusão. A
# identidade real é o sha256 do conteúdo (ver edgetelemetry.sha_linha): número de
# linha se desloca — o arquivo do dia recebe escrita contínua do servidor vivo
# (foi de 31.082 para 31.139 linhas durante a própria auditoria).
sha_linha = edgetelemetry.sha_linha


def caminho_quarentena(root):
    return os.path.join(root, "data", "ops", "access_ledger_quarantine.jsonl")


def dir_membros(root):
    return os.path.join(root, "data", "ops", "access_ledger_quarantine_members")


def _instante(ts):
    """'2026-08-12T06:32:07Z' -> datetime. Devolve None se o campo nao servir."""
    if not isinstance(ts, str):
        return None
    try:
        return datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def ler(caminho):
    """Percorre um arquivo do ledger devolvendo (numero, bruto, registro).

    Linha em branco é pulada. Linha com JSON quebrado é devolvida com
    registro=None em vez de sumir: quem chama decide o que fazer com ela, e
    nenhum leitor deste módulo tem licença para esconder o que não conseguiu ler.
    """
    if not os.path.isfile(caminho):
        return
    with open(caminho, encoding="utf-8") as handle:
        for numero, bruto in enumerate(handle, start=1):
            bruto = bruto.strip()
            if not bruto:
                continue
            try:
                registro = json.loads(bruto)
            except json.JSONDecodeError:
                yield numero, bruto, None
                continue
            yield numero, bruto, registro


def carregar_quarentena(root):
    """Devolve (entradas, hashes, problemas).

    entradas  — lista dos registros do ledger de quarentena, em ordem de leitura.
    hashes    — conjunto dos sha256 de linha efetivamente neutralizados.
    problemas — inconsistências que o CHECK deve reprovar em vez de engolir: lote
                sem arquivo de membros, arquivo de membros com digest diferente
                do declarado, contagem que não bate. Uma quarentena que não se
                verifica é uma licença aberta para excluir qualquer linha, e isso
                seria pior do que o defeito que ela veio fechar.
    """
    entradas = []
    hashes = set()
    problemas = []
    caminho = caminho_quarentena(root)
    if not os.path.isfile(caminho):
        return entradas, hashes, problemas

    for numero, bruto, registro in ler(caminho):
        if registro is None:
            problemas.append("quarentena linha %d: JSON invalido" % numero)
            continue
        entradas.append(registro)
        lote = registro.get("batch_id") or "(sem batch_id)"
        arquivo = os.path.join(dir_membros(root), registro.get("members_file") or "")
        if not registro.get("members_file") or not os.path.isfile(arquivo):
            problemas.append(
                "lote %s: arquivo de membros ausente (%s) — sem a lista de hashes "
                "nao ha como excluir exatamente as linhas revisadas"
                % (lote, registro.get("members_file")))
            continue
        with open(arquivo, encoding="utf-8") as handle:
            membros = [linha.strip() for linha in handle if linha.strip()]
        digest = digest_membros(membros)
        if digest != registro.get("members_sha256"):
            problemas.append(
                "lote %s: digest dos membros nao confere (arquivo=%s declarado=%s) "
                "— a lista foi editada depois de revisada"
                % (lote, digest, registro.get("members_sha256")))
            continue
        if len(membros) != registro.get("member_count"):
            problemas.append(
                "lote %s: %d hashes no arquivo, %s declarados em member_count"
                % (lote, len(membros), registro.get("member_count")))
            continue
        hashes.update(membros)
    return entradas, hashes, problemas


def digest_membros(membros):
    """Digest estavel do CONJUNTO de linhas de um lote.

    Ordenar antes de somar é o que torna o digest independente da ordem em que
    as linhas foram lidas; duplicatas byte-idênticas são preservadas (mesma
    convenção da quarentena da borda: duas linhas iguais compartilham o hash de
    propósito, e uma entrada neutraliza as duas).
    """
    return edgetelemetry.sha_linha("\n".join(sorted(membros)))


def sessoes(caminho, ignorar=frozenset()):
    """Agrupa as linhas NAO-declaradas-sinteticas do arquivo em sessoes.

    Sessão = mesmo User-Agent, requisições consecutivas com intervalo <=
    JANELA_SESSAO_S. Linha com `warming` ou `bot_simulation` verdadeiros fica de
    fora: já se declarou sintética e não precisa de detector. Hash em `ignorar`
    (tipicamente a quarentena já gravada) também fica de fora, que é o que
    permite ao check dizer "não sobrou contaminação por reconhecer".
    """
    por_agente = {}
    for numero, bruto, registro in ler(caminho):
        if registro is None:
            continue
        if registro.get("warming") or registro.get("bot_simulation"):
            continue
        if sha_linha(bruto) in ignorar:
            continue
        quando = _instante(registro.get("ts"))
        if quando is None:
            continue
        agente = registro.get("user_agent") or ""
        por_agente.setdefault(agente, []).append((quando, numero, bruto, registro))

    resultado = []
    for agente, linhas in por_agente.items():
        linhas.sort(key=lambda item: (item[0], item[1]))
        atual = [linhas[0]]
        for item in linhas[1:]:
            if (item[0] - atual[-1][0]).total_seconds() <= JANELA_SESSAO_S:
                atual.append(item)
            else:
                resultado.append(_montar_sessao(caminho, agente, atual))
                atual = [item]
        resultado.append(_montar_sessao(caminho, agente, atual))
    resultado.sort(key=lambda s: (s["ts_start"], s["user_agent"]))
    return resultado


def _montar_sessao(caminho, agente, itens):
    caminhos_pedidos = {item[3].get("path") for item in itens}
    duracao = (itens[-1][0] - itens[0][0]).total_seconds()
    return {
        "source_file": os.path.basename(caminho),
        "user_agent": agente,
        "ts_start": itens[0][3].get("ts"),
        "ts_end": itens[-1][3].get("ts"),
        "span_seconds": duracao,
        "line_count": len(itens),
        "distinct_paths": len(caminhos_pedidos),
        "page_lines": sum(1 for item in itens if item[3].get("route_class") == "page"),
        # max(duracao, 1) evita divisao por zero quando a sessao inteira cai no
        # mesmo segundo; o efeito e SUBESTIMAR a taxa, nunca inflar.
        "requests_per_second": len(itens) / max(duracao, 1.0),
        "sweep_ratio": len(caminhos_pedidos) / len(itens),
        "bot_rules": sorted({item[3].get("bot_rule") or "" for item in itens}),
        "line_sha256": [sha_linha(item[2]) for item in itens],
        "lines": [item[1] for item in itens],
    }


def avaliar_sessao(sessao, acervo):
    """Motivos pelos quais a sessao so pode ter sido gerada pelo proprio projeto.

    Lista vazia = plausível como tráfego. Cada motivo carrega o número medido e
    o teto, para que a reprovação possa ser conferida sem abrir o código.
    """
    motivos = []
    varredura = sessao["sweep_ratio"] >= MIN_RAZAO_VARREDURA

    if (sessao["line_count"] >= MIN_LINHAS_RAJADA
            and sessao["requests_per_second"] >= MIN_TAXA_RAJADA_RPS
            and varredura):
        motivos.append(
            "varredura em rajada: %d linhas em %.0fs (%.1f req/s, teto %.0f) com "
            "razao de varredura %.2f (teto %.2f) — maior sessao real medida no "
            "corpus: 297 linhas a 4,8 req/s"
            % (sessao["line_count"], sessao["span_seconds"],
               sessao["requests_per_second"], MIN_TAXA_RAJADA_RPS,
               sessao["sweep_ratio"], MIN_RAZAO_VARREDURA))

    if acervo > edgetelemetry.ACERVO_DESCONHECIDO and varredura:
        cobertura = sessao["distinct_paths"] / acervo
        if cobertura >= MIN_COBERTURA_ACERVO:
            motivos.append(
                "enumeracao do acervo: %d URLs distintas = %.0f%% das %d publicas "
                "(teto %.0f%%) numa sessao so — desde o cutover de 2026-08-06 o "
                "acervo sai do disco pelo nginx e nao passa por este log, entao "
                "so o proprio projeto consegue enumera-lo aqui; maior cobertura "
                "real medida: 1,3%%"
                % (sessao["distinct_paths"], 100.0 * cobertura, acervo,
                   100.0 * MIN_COBERTURA_ACERVO))
    return motivos


def arquivos_do_ledger(root):
    diretorio = os.path.join(root, "data", "ops", "access")
    if not os.path.isdir(diretorio):
        return []
    return [os.path.join(diretorio, nome) for nome in sorted(os.listdir(diretorio))
            if nome.startswith("access-") and nome.endswith(".jsonl")]


def detectar(root, hashes_ignorados=frozenset()):
    """Todas as sessoes contaminadas ainda NAO reconhecidas, por arquivo."""
    acervo = edgetelemetry.acervo_urls(root)
    achados = []
    for caminho in arquivos_do_ledger(root):
        for sessao in sessoes(caminho, ignorar=hashes_ignorados):
            motivos = avaliar_sessao(sessao, acervo)
            if motivos:
                sessao = dict(sessao)
                sessao["reasons"] = motivos
                achados.append(sessao)
    return achados, acervo


def detectar_rota_interna(root, hashes_ignorados=frozenset()):
    """Linhas de rota que o ingress bloqueia — sinteticas por construcao.

    Independe de sessao, de taxa e de volume: uma unica linha ja reprova, porque
    o veredito nao vem de um limiar e sim da topologia (ver
    ROTAS_BLOQUEADAS_NO_INGRESS). Agrupa por arquivo e rota so para o relatorio
    ficar legivel; a unidade de reconhecimento continua sendo o sha256 da linha,
    igual ao resto do modulo.

    Linha ja quarentenada nao aparece — reconhecer e o que tira da conta. Linha
    com `warming` ou `bot_simulation` tambem nao: quem se declarou sintetico nao
    precisa de detector. Sobra exatamente o que se apresenta como trafego real.
    """
    achados = []
    for caminho in arquivos_do_ledger(root):
        por_rota = {}
        for _numero, bruto, registro in ler(caminho):
            if registro is None:
                continue
            rota = registro.get("path")
            if rota not in ROTAS_BLOQUEADAS_NO_INGRESS:
                continue
            if registro.get("warming") or registro.get("bot_simulation"):
                continue
            if sha_linha(bruto) in hashes_ignorados:
                continue
            grupo = por_rota.setdefault(rota, {
                "source_file": os.path.basename(caminho),
                "path": rota,
                "line_count": 0,
                "ts_start": registro.get("ts"),
                "ts_end": registro.get("ts"),
                "user_agents": set(),
                "line_sha256": [],
            })
            grupo["line_count"] += 1
            grupo["ts_end"] = registro.get("ts")
            grupo["user_agents"].add(registro.get("user_agent") or "")
            grupo["line_sha256"].append(sha_linha(bruto))
        for grupo in por_rota.values():
            grupo["user_agents"] = sorted(grupo["user_agents"])
            grupo["reasons"] = [
                "rota bloqueada no ingress: %s respondeu %d vez(es) neste log, mas o "
                "nginx devolve 404 nela antes de chegar ao Go "
                "(ops/nginx/wikijuridica.conf:384) — nenhum cliente externo "
                "consegue produzir esta linha; ela nasceu dentro do processo"
                % (grupo["path"], grupo["line_count"])
            ]
            achados.append(grupo)
    return achados


# ────────────────────────────────────────────────────────────────────────────
# A SEGUNDA FONTE: o ledger do NGINX (2026-09-03)
#
# Tudo acima lê `access-YYYY-MM-DD.jsonl`, escrito PELO PROCESSO GO. Duas
# cegueiras medidas:
#   • ele para quando o Go para (17 h sem uma linha em 01-02/09/2026);
#   • ele não vê o acervo HTML, que sai estático do disco pelo nginx. Em
#     2026-09-02 o ledger do Go tinha 742 requisições reais e o do nginx 8.729,
#     das quais 7.230 eram páginas do acervo — 2.007 do PerplexityBot.
#
# `tools/generate-origin-access-ledger` transcreve o log do nginx para
# `nginx-YYYY-MM-DD.jsonl`, no mesmo vocabulário. As funções abaixo dão acesso a
# essa fonte SEM fundir as duas: uma requisição que passa pelo Go aparece nos
# dois arquivos, e somá-las contaria duas vezes. Quem precisa de cobertura total
# (páginas, 404, bot de IA no acervo) usa `linhas_do_nginx`; quem mede rota
# dinâmica continua no ledger do Go. `idade_do_ledger_go` existe para o leitor
# poder dizer INCONCLUSIVO em vez de "zero" quando a fonte parou.

def arquivos_do_ledger_nginx(root):
    """Os JSONL transcritos do log do nginx, do mais antigo para o mais novo."""
    # `dir_membros` é o diretório da QUARENTENA, não o do ledger — o ledger vive
    # em data/ops/access/, que é de onde `arquivos_do_ledger` lê.
    padrao = _os.path.join(root, "data", "ops", "access", "nginx-*.jsonl")
    return sorted(_glob.glob(padrao))


def idade_do_ledger_go(root, agora=None):
    """Horas desde a última escrita do ledger do Go, ou None se não houver.

    Acima de ~2 h significa que o processo não está registrando (ele grava a
    cada 3 s quando há tráfego, e há tráfego o tempo todo): quem consome a série
    deve sair INCONCLUSIVO, nunca concluir "nenhum bot veio".
    """
    arquivos = arquivos_do_ledger(root)
    if not arquivos:
        return None
    agora = agora or _dt.datetime.now(_dt.timezone.utc)
    try:
        mtime = _dt.datetime.fromtimestamp(_os.path.getmtime(arquivos[-1]), _dt.timezone.utc)
    except OSError:
        return None
    return (agora - mtime).total_seconds() / 3600.0


def linhas_do_nginx(root, dias=0, hoje=None):
    """Requisições REAIS vistas pelo nginx (o produtor já descartou as próprias).

    Mesma assinatura de `linhas_saneadas` para que trocar de fonte seja trocar o
    nome da função. Não aplica a quarentena do ledger do Go: a contaminação que
    ela existe para conter (harness de teste escrevendo no ledger em processo)
    não alcança o log do nginx, que só registra o que passou por um socket.
    """
    hoje = hoje or _dt.datetime.now(_dt.timezone.utc).date()
    limite = None
    if dias:
        limite = (hoje - _dt.timedelta(days=dias - 1)).isoformat()
    saida = []
    for caminho in arquivos_do_ledger_nginx(root):
        dia = _os.path.basename(caminho)[len("nginx-"):-len(".jsonl")]
        if limite and dia < limite:
            continue
        try:
            with open(caminho, encoding="utf-8") as handle:
                for bruto in handle:
                    bruto = bruto.strip()
                    if not bruto:
                        continue
                    try:
                        saida.append(_json.loads(bruto))
                    except ValueError:
                        continue
        except OSError:
            continue
    return saida


def linhas_saneadas(root, dias=0, incluir_sinteticos=False, hoje=None):
    """O ledger como um consumidor honesto deve le-lo.

    Devolve (registros, resumo). O resumo conta separadamente o que saiu por
    cada motivo — quarentena, aquecimento, simulação —, porque número excluído
    em silêncio é a mesma classe de problema que número inflado: quem lê o
    relatório precisa ver que houve exclusão e por quê.
    """
    _entradas, hashes, problemas = carregar_quarentena(root)
    corte = None
    if dias:
        base = hoje or datetime.date.today()
        corte = (base - datetime.timedelta(days=dias)).isoformat()

    registros = []
    resumo = {
        "quarantined_excluded": 0,
        "warming_excluded": 0,
        "simulation_excluded": 0,
        "quarantine_problems": problemas,
        "quarantine_hashes": len(hashes),
    }
    for caminho in arquivos_do_ledger(root):
        dia = os.path.basename(caminho)[len("access-"):-len(".jsonl")]
        if corte and dia < corte:
            continue
        for _numero, bruto, registro in ler(caminho):
            if registro is None:
                continue
            # A quarentena vale SEMPRE, inclusive sob --incluir-sinteticos: o
            # que ela retira nao e "tipo de trafego que o operador pode querer
            # ver", e linha que o projeto ja reconheceu como forjada.
            if sha_linha(bruto) in hashes:
                resumo["quarantined_excluded"] += 1
                continue
            if not incluir_sinteticos:
                if registro.get("warming"):
                    resumo["warming_excluded"] += 1
                    continue
                if registro.get("bot_simulation"):
                    resumo["simulation_excluded"] += 1
                    continue
            registros.append(registro)
    return registros, resumo
