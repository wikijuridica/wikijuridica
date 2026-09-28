#!/usr/bin/env python3
"""Testes de tools/purge-origin-cache — a invalidação do cache de origem.

POR QUE ESTES TESTES EXISTEM (2026-09-05, refeitos em 2026-09-16)
------------------------------------------------------------------
A ferramenta nasceu de um defeito medido: o binário do servidor passou a emitir
campos novos no front matter da gêmea, o restart entrou, o Go passou a servi-los
— e o nginx continuou entregando a versão anterior por servir da zona `wj_dyn`,
cujo `s-maxage` para essas rotas é de SETE DIAS.

A PRIMEIRA VERSÃO DESTES TESTES FAZIA PARTE DO DEFEITO. Eles cobravam que a
ferramenta REPRODUZISSE a `proxy_cache_key` do nginx — um deles exigia, com
nome e tudo, que ela montasse a chave do host `127.0.0.1:8088`. Medido na zona
viva em 2026-09-16: das 13.738 chaves, NENHUMA tem `:8088` e NENHUMA tem
`https`; o `$host` do nginx não carrega porta. O teste exigia cobertura de uma
chave que não existe e nunca cobrava o que importa — que, DEPOIS da invalidação,
não sobre objeto daquela rota na zona. A ferramenta apagava 1 de 2 ou 3 objetos
e os testes ficavam verdes.

O que muda aqui: o teste passa a medir CONJUNTO (quantos objetos da rota
sobraram), não fórmula. O acoplamento com o `.conf` continua — mas agora sobre o
PARSER da chave, que é a parte que de fato precisa acompanhar o vhost.

Uso: python3 tools/test_purge_origin_cache.py
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True  # mutante e original têm de ser sempre lidos da fonte

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FERRAMENTA = pathlib.Path(os.environ.get("PURGE_ORIGIN_CACHE_BIN",
                                         str(RAIZ / "tools" / "purge-origin-cache")))
NGINX_CONF = RAIZ / "ops" / "nginx" / "wikijuridica.conf"
NGINX_VIVO = RAIZ / "ops" / "nginx" / "standalone" / "nginx.conf"
ZONA_VIVA = RAIZ / "var" / "nginx" / "cache"

# O cabeçalho binário do objeto de cache (ngx_http_file_cache_header_t) no nginx
# 1.22.1 desta máquina: medido em 2026-09-16, a linha `\nKEY: ` começa no byte
# 336 de todo objeto da zona. O conteúdo dele não importa para a ferramenta —
# ela procura a marca `\nKEY: ` —, mas o TAMANHO importa: é o que põe a chave
# fora dos primeiros bytes e obriga a leitura de um prefixo maior.
CABECALHO_BINARIO = 336


def carrega_modulo(caminho=FERRAMENTA):
    nome = "purge_origin_cache_" + hashlib.md5(str(caminho).encode()).hexdigest()[:8]  # noqa: S324
    spec = importlib.util.spec_from_loader(
        nome, importlib.machinery.SourceFileLoader(nome, str(caminho)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FALHAS = []


def verifica(condicao, descricao):
    marca = "ok  " if condicao else "FALHA"
    print(f"  {marca} {descricao}")
    if not condicao:
        FALHAS.append(descricao)


# ------------------------------------------------------------------ fixture

def escreve_objeto(cache: pathlib.Path, nome_md5: str, chave: str, corpo: bytes = b"corpo"):
    """Escreve um objeto no layout REAL do nginx: cabeçalho binário, `\\nKEY: `, HTTP, corpo."""
    destino = cache / nome_md5[-1] / nome_md5[-3:-1] / nome_md5
    destino.parent.mkdir(parents=True, exist_ok=True)
    conteudo = (b"\x00" * CABECALHO_BINARIO
                + b"\nKEY: " + chave.encode("utf-8") + b"\n"
                + b"HTTP/1.1 200 OK\r\nVary: Accept-Encoding, Accept\r\n\r\n" + corpo)
    destino.write_bytes(conteudo)
    return destino


def zona_de_teste(cache: pathlib.Path, chave: str, encodings=("gzip, br", "")):
    """Uma chave com o objeto PRINCIPAL e uma variante de Vary por encoding.

    É o layout que a zona viva tem em 11.189 das 13.738 chaves. O nome da
    variante é `md5(md5_bruto(chave) + b"accept-encoding:" + valor + b"\\r\\n")`,
    reproduzido byte a byte contra a zona viva em 2026-09-16.
    """
    principal = hashlib.md5(chave.encode()).hexdigest()  # noqa: S324
    bruto = hashlib.md5(chave.encode()).digest()  # noqa: S324
    escritos = [escreve_objeto(cache, principal, chave)]
    for ae in encodings:
        nome = hashlib.md5(bruto + b"accept-encoding:" + ae.encode() + b"\r\n").hexdigest()  # noqa: S324
        escritos.append(escreve_objeto(cache, nome, chave))
    return escritos


# ------------------------------------------------------------------ testes

def test_remove_todas_as_variantes_da_rota(mod, tmp):
    """O TESTE PRINCIPAL: depois da invalidação, ZERO objeto da rota na zona.

    É o que a versão por fórmula não fazia — ela alcançava só `md5(chave)` e
    deixava as variantes de `Vary: Accept-Encoding` servindo o corpo anterior.
    """
    cache = pathlib.Path(tmp) / "cache_variantes"
    chave = "fb:httpwikijuridica.com.br/noticias/x-20260914/index.md:0"
    escritos = zona_de_teste(cache, chave)
    verifica(len(escritos) == 3, f"a fixture tem principal + 2 variantes (tem {len(escritos)})")
    verifica(all(p.exists() for p in escritos), "os 3 objetos existem antes")

    rel = mod.invalida(["/noticias/x-20260914/index.md"], cache=cache)
    verifica(rel["objetos_antes"] == 3, f"encontrou os 3 objetos da rota (achou {rel['objetos_antes']})")
    verifica(rel["removidos"] == 3, f"removeu os 3 (removeu {rel['removidos']})")
    verifica(rel["restantes"] == 0, "nenhum objeto resistiu")
    sobraram = [p for p in escritos if p.exists()]
    verifica(not sobraram, f"ZERO objeto da rota sobrou na zona (sobraram {len(sobraram)})")


def test_alcanca_as_duas_locations_e_a_query(mod, tmp):
    """@markdown (`md:`) e @fallback (`fb:`) servem a MESMA URI com chaves distintas,
    e o `$request_uri` carrega a query — há objeto vivo com `?wjdiag=`."""
    cache = pathlib.Path(tmp) / "cache_locations"
    rota = "/noticias/y-20260914/index.md"
    chaves = ["md:httpwikijuridica.com.br" + rota,
              "fb:httpwikijuridica.com.br" + rota + ":0",
              "fb:httpwikijuridica.com.br" + rota + "?wjdiag=1:0",
              "fb:http127.0.0.1" + rota + ":0"]
    for chave in chaves:
        zona_de_teste(cache, chave, encodings=("gzip, br",))
    rel = mod.invalida([rota], cache=cache)
    verifica(rel["objetos_antes"] == 8,
             f"alcançou as 4 chaves x 2 objetos (achou {rel['objetos_antes']})")
    verifica(rel["removidos"] == 8 and rel["restantes"] == 0, "removeu todos, sem restante")
    por_rota = rel["rotas"][0]
    verifica(len(por_rota["chaves"]) == 4,
             f"registrou as 4 chaves distintas da rota (registrou {len(por_rota['chaves'])})")
    verifica(any("127.0.0.1" in c for c in por_rota["chaves"]),
             "alcançou a chave de host local SEM porta — a que a lista fixa nunca montava")


def test_nao_toca_rota_vizinha(mod, tmp):
    """Falso positivo: `/a/b/index.md` não pode levar `/a/b-2/index.md` junto."""
    cache = pathlib.Path(tmp) / "cache_vizinha"
    zona_de_teste(cache, "fb:httpwikijuridica.com.br/noticias/z-20260914/index.md:0")
    vizinhos = zona_de_teste(cache, "fb:httpwikijuridica.com.br/noticias/z-20260914-extra/index.md:0")
    rel = mod.invalida(["/noticias/z-20260914/index.md"], cache=cache)
    verifica(rel["removidos"] == 3, f"removeu só os 3 da rota pedida (removeu {rel['removidos']})")
    verifica(all(p.exists() for p in vizinhos), "os objetos da rota vizinha continuam na zona")


def test_verifica_ausencia_e_reprova(mod, tmp):
    """`restantes > 0` tem de reprovar: dizer que invalidou sem conferir é o
    defeito de família que este repositório já pagou duas vezes."""
    cache = pathlib.Path(tmp) / "cache_ausencia"
    chave = "fb:httpwikijuridica.com.br/noticias/w-20260914/index.md:0"
    zona_de_teste(cache, chave)
    remove_real = os.remove
    try:
        os.remove = lambda caminho: None  # o objeto continua no disco
        rel = mod.invalida(["/noticias/w-20260914/index.md"], cache=cache)
    finally:
        os.remove = remove_real
    verifica(rel["restantes"] == 3, f"contou os 3 objetos que resistiram (contou {rel['restantes']})")
    verifica(rel["removidos"] == 0, "nenhum foi contado como removido")
    codigo = subprocess.run([sys.executable, str(FERRAMENTA), "--rota", "/x/index.md",
                             "--cache", str(cache)], capture_output=True, text=True, timeout=120)
    verifica(codigo.returncode == 0, "rota sem objeto continua exit 0 (não é erro)")


def test_recusa_apagar_tudo():
    """Sem rota, a ferramenta tem de RECUSAR. Varrer a zona destruiria o use_stale
    de todas as rotas dinâmicas, que é a rede que segura o canal quando o Go cai."""
    p = subprocess.run([sys.executable, str(FERRAMENTA)], capture_output=True, text=True, timeout=120)
    verifica(p.returncode != 0, "sem rota, a ferramenta recusa (exit != 0)")
    verifica("apagar tudo" in (p.stderr + p.stdout),
             "a recusa explica por que não existe modo 'apagar tudo'")


def test_seco_nao_remove(tmp):
    """--seco tem de listar sem tocar no disco."""
    cache = pathlib.Path(tmp) / "cache_seco"
    escritos = zona_de_teste(cache, "fb:httpwikijuridica.com.br/rota-de-teste/index.md:0")
    ledger = pathlib.Path(tmp) / "seco.jsonl"
    p = subprocess.run([sys.executable, str(FERRAMENTA), "--rota", "/rota-de-teste/index.md",
                        "--cache", str(cache), "--ledger", str(ledger), "--seco"],
                       capture_output=True, text=True, timeout=120)
    verifica(p.returncode == 0, "--seco sai 0")
    verifica("seriam removidos" in p.stdout, "--seco relata em modo condicional, nunca como feito")
    verifica(all(x.exists() for x in escritos), "--seco não removeu nenhum objeto")
    verifica(not ledger.exists(), "--seco não escreve no ledger")


def test_json_e_ledger_por_objeto(tmp):
    """O ledger tinha UMA linha por rota e a zona tinha 2 a 3 objetos por rota:
    era a linha que escondia o defeito. Agora é uma linha por OBJETO."""
    cache = pathlib.Path(tmp) / "cache_ledger"
    ledger = pathlib.Path(tmp) / "purga.jsonl"
    zona_de_teste(cache, "fb:httpwikijuridica.com.br/noticias/v-20260914/index.md:0")
    p = subprocess.run([sys.executable, str(FERRAMENTA), "--rota", "/noticias/v-20260914/index.md",
                        "--cache", str(cache), "--ledger", str(ledger), "--json"],
                       capture_output=True, text=True, timeout=120)
    verifica(p.returncode == 0, "exit 0 quando removeu tudo")
    rel = json.loads(p.stdout)
    verifica(rel["removidos"] == 3 and rel["restantes"] == 0,
             f"o JSON traz removidos=3 restantes=0 (traz {rel['removidos']}/{rel['restantes']})")
    linhas = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    verifica(len(linhas) == 3, f"o ledger tem UMA linha por objeto (tem {len(linhas)})")
    verifica(sum(1 for l in linhas if l["objeto_principal"]) == 1,
             "exatamente uma das linhas é o objeto principal; as outras são variantes")


def test_parser_da_chave_bate_com_a_config_real(mod):
    """O ACOPLAMENTO, agora sobre o parser. Se a `proxy_cache_key` do vhost mudar
    de forma, é aqui que reprova — e o que se cobra é a ROTA extraída, não uma
    lista de hosts que a ferramenta tenha de adivinhar."""
    for conf in (NGINX_CONF, NGINX_VIVO):
        if not conf.exists():
            continue
        declaradas = re.findall(r'proxy_cache_key\s+"([^"]+)"', conf.read_text(encoding="utf-8"))
        verifica(len(declaradas) >= 2,
                 f"{conf.name} declara ao menos duas proxy_cache_key (achadas: {len(declaradas)})")
        rota = "/autonomos/exemplo/index.md"
        for declarada in declaradas:
            # O `://` fica: a zona da rede social declara a chave nessa forma,
            # sem prefixo, e o parser tem de cobrir as duas.
            concreta = (declarada
                        .replace("$scheme", "http")
                        .replace("$host", "wikijuridica.com.br")
                        .replace("$proxy_host", "wikijuridica.com.br")
                        .replace("$request_uri", rota)
                        .replace("$wj_markdown", "0"))
            _, uri = mod.uri_da_chave(concreta)
            verifica(uri == rota,
                     f"{conf.name}: a ferramenta extrai a rota da chave {concreta!r} (extraiu {uri!r})")


def test_variante_do_nginx_reproduz_a_medicao(mod, tmp):
    """O hash de variante medido na zona viva em 2026-09-16. Documenta o mecanismo
    que a fórmula sozinha não alcança — e é o que a fixture usa."""
    chave = "fb:httpwikijuridica.com.br/noticias/cjf-20260820/index.md:0"
    cache = pathlib.Path(tmp)
    verifica(mod.caminho_do_objeto(chave, cache).name == "0c3cd4f1a974682839f881971b9792b2",
             "o objeto principal é o md5 da chave (medido na zona viva)")
    verifica(mod.caminho_da_variante(chave, "", cache).name == "9810fcb2a768a9ed2f307a1783c32b1a",
             "a variante de Accept-Encoding vazio bate com o objeto medido na zona viva")
    verifica(mod.caminho_da_variante(chave, "", cache) != mod.caminho_do_objeto(chave, cache),
             "variante e principal são arquivos DIFERENTES — a razão de existir desta correção")


def test_principal_fora_do_indice_reprova(mod, tmp):
    """Se a varredura deixar de enxergar um objeto que a fórmula acha no disco —
    subdiretório ilegível, parser de chave quebrado —, a ferramenta tem de
    GRITAR, não apagar menos em silêncio. É a única parte do nome que se deriva
    da chave, e por isso serve de autoconsistência da varredura."""
    cache = pathlib.Path(tmp) / "cache_parser"
    chave = "fb:httpwikijuridica.com.br/noticias/u-20260914/index.md:0"
    zona_de_teste(cache, chave)
    rel = mod.invalida(["/noticias/u-20260914/index.md"], cache=cache)
    verifica(rel["removidos"] == 3 and not rel["principal_fora_do_indice"],
             "com a varredura boa, nada cai na autoconsistência")

    # A varredura passa a não enxergar o objeto principal (o efeito de um
    # diretório que o processo não consegue ler). Ele continua no disco.
    cache2 = pathlib.Path(tmp) / "cache_parser_cego"
    zona_de_teste(cache2, chave)
    principal = mod.caminho_do_objeto(chave, cache2).name
    walk_real = os.walk

    def walk_cego(topo, *a, **kw):
        for pasta, dirs, arquivos in walk_real(topo, *a, **kw):
            yield pasta, dirs, [f for f in arquivos if f != principal]

    try:
        os.walk = walk_cego
        rel2 = mod.invalida(["/noticias/u-20260914/index.md"], cache=cache2)
    finally:
        os.walk = walk_real
    verifica(len(rel2["principal_fora_do_indice"]) == 1,
             f"objeto principal no disco e fora do índice é denunciado "
             f"(denunciou {len(rel2['principal_fora_do_indice'])})")
    verifica(mod.caminho_do_objeto(chave, cache2).exists(),
             "e o objeto que a varredura não viu continua lá — é isso que a denúncia significa")


def test_objeto_sem_chave_nao_some_da_conta(mod, tmp):
    """Arquivo na zona sem linha KEY legível é contado e relatado — não ignorado."""
    cache = pathlib.Path(tmp) / "cache_sem_chave"
    destino = cache / "a" / "bc" / "deadbeef"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(b"\x00" * 64)
    rel = mod.invalida(["/qualquer/index.md"], cache=cache)
    verifica(rel["objetos_sem_chave"] == 1,
             f"o arquivo ilegível entra em objetos_sem_chave (entrou {rel['objetos_sem_chave']})")


def test_rotas_de_area_saem_do_acervo(mod):
    """A lista de áreas é DERIVADA de content/pages.json, nunca fixa no código:
    lista fixa envelhece no dia em que uma área nasce."""
    rotas = mod.rotas_de_area()
    verifica(len(rotas) > 5, f"derivou mais de 5 áreas do acervo (achou {len(rotas)})")
    verifica(all(r.startswith("/") and r.endswith("/index.md") for r in rotas),
             "toda rota de área tem a forma /{area}/index.md")
    verifica(len(rotas) == len(set(rotas)), "sem área repetida")


def test_layout_da_zona_viva(mod):
    """Acoplamento com o formato do objeto: a marca `KEY:` tem de estar dentro do
    prefixo que a ferramenta lê. Só roda onde a zona existe, e só lê."""
    if not ZONA_VIVA.is_dir():
        print("  --   zona viva ausente; teste de layout pulado")
        return
    lidos = 0
    for pasta, _, arquivos in os.walk(ZONA_VIVA):
        for nome in arquivos:
            with open(os.path.join(pasta, nome), "rb") as fh:
                cabecalho = fh.read(mod.PREFIXO_LIDO)
            achou = mod.MARCA_CHAVE.search(cabecalho)
            verifica(bool(achou), f"objeto real {nome}: a linha KEY cabe nos {mod.PREFIXO_LIDO} bytes lidos")
            if achou:
                _, uri = mod.uri_da_chave(achou.group(1).decode("utf-8", "replace"))
                verifica(uri is not None and uri.startswith("/"),
                         f"objeto real {nome}: o parser extrai a URI ({uri!r})")
            lidos += 1
            if lidos >= 3:
                return
        if lidos >= 3:
            return


def main() -> int:
    if not FERRAMENTA.exists():
        raise SystemExit(f"ferramenta ausente: {FERRAMENTA}")
    mod = carrega_modulo()
    with tempfile.TemporaryDirectory() as tmp:
        print("remoção de TODAS as variantes da rota:")
        test_remove_todas_as_variantes_da_rota(mod, tmp)
        print("as duas locations, host local e query:")
        test_alcanca_as_duas_locations_e_a_query(mod, tmp)
        print("falso positivo em rota vizinha:")
        test_nao_toca_rota_vizinha(mod, tmp)
        print("verificação de ausência:")
        test_verifica_ausencia_e_reprova(mod, tmp)
        print("recusa de apagar tudo:")
        test_recusa_apagar_tudo()
        print("modo seco:")
        test_seco_nao_remove(tmp)
        print("JSON e ledger por objeto:")
        test_json_e_ledger_por_objeto(tmp)
        print("acoplamento com a config real do nginx:")
        test_parser_da_chave_bate_com_a_config_real(mod)
        print("hash de variante do nginx:")
        test_variante_do_nginx_reproduz_a_medicao(mod, tmp)
        print("autoconsistência da varredura:")
        test_principal_fora_do_indice_reprova(mod, tmp)
        print("objeto ilegível na zona:")
        test_objeto_sem_chave_nao_some_da_conta(mod, tmp)
        print("rotas de área:")
        test_rotas_de_area_saem_do_acervo(mod)
        print("layout da zona viva:")
        test_layout_da_zona_viva(mod)

    print(f"\n{len(FALHAS)} falha(s)")
    if FALHAS:
        for f in FALHAS:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
