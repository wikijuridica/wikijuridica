"""wikiuniverso — a fonte única do "universo público" do portal.

★ POR QUE EXISTE (2026-08-29, FAMÍLIA-A da caça aos bugs)

Medido: 42 arquivos de `tools/`, `cmd/` e `internal/` liam `public/sitemaps/`
DIRETAMENTE DO DISCO para saber quais URLs o portal publica. O diretório não é
uma lista de URLs publicadas — é um depósito com três populações misturadas:

  62 arquivos .xml   → 34 declarados no índice + 28 shards em CARÊNCIA
  58 arquivos .br    → gêmeas comprimidas, que não são XML

A carência é deliberada e correta: shard retirado do índice continua servindo
200 por alguns dias, para não dar 404 a um crawler que ainda tem o índice
anterior. Quem lê o diretório, porém, soma as três populações e erra por dois
caminhos diferentes:

  Classe A — lista sem filtrar extensão e estoura no primeiro .br.
             `check-internal-link-floor` morria com
             "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1", e o
             exit 1 resultante era lido como "reprovou por conteúdo".

  Classe B — filtra *.xml mas conta os 62, não os 34. O universo inflava de
             10.336 para 18.772 URLs (+81,6%). Isso matou o aquecedor de borda
             por timeout duas noites seguidas e fez o alerta de cobertura dizer
             ao dono que "~18.726 páginas devolveriam 530 se o túnel cair",
             quando o número real é 10.336.

A correção não é remendar os 42 leitores: é ter UMA definição de universo
público, derivada de onde a verdade mora — `public/sitemap.xml`, que é o
documento que o portal de fato anuncia aos buscadores.

★ O QUE ESTA FUNÇÃO GARANTE

- Deriva do ÍNDICE, nunca do diretório: shard em carência não entra.
- Só lê o que o índice declara; `.br` e arquivo solto são invisíveis por
  construção, não por filtro de extensão que alguém pode esquecer de repetir.
- Shard declarado e ausente do disco é ERRO, não silêncio: é 404 anunciado ao
  Googlebot, e o chamador precisa saber.
- Devolve ordem estável e sem duplicata.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

INDICE_REL = os.path.join("public", "sitemap.xml")
SHARDS_DIR_REL = os.path.join("public", "sitemaps")

_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class UniversoIndisponivel(RuntimeError):
    """O índice não pôde ser lido, ou anuncia shard que não existe no disco."""


def _texto_locs(xml_bytes: bytes) -> list[str]:
    """Extrai <loc> tolerando namespace ausente e prólogo malformado."""
    try:
        raiz = ET.fromstring(xml_bytes)
    except ET.ParseError:
        # Fallback textual: um shard com prólogo estranho ainda é servido pelo
        # nginx, então ignorá-lo aqui esconderia URL que o crawler enxerga.
        return [m.group(1).strip() for m in re.finditer(rb"<loc>(.*?)</loc>", xml_bytes, re.S)
                for m in [type("m", (), {"group": lambda self, i, _v=m: _v.group(i).decode("utf-8", "replace")})()]]
    saida = []
    for elemento in raiz.iter():
        if elemento.tag in (f"{_NS}loc", "loc") and elemento.text:
            saida.append(elemento.text.strip())
    return saida


def shards_declarados(raiz_projeto: str) -> list[str]:
    """Nomes de arquivo dos shards que o índice vivo anuncia."""
    indice = os.path.join(raiz_projeto, INDICE_REL)
    try:
        with open(indice, "rb") as fh:
            conteudo = fh.read()
    except OSError as erro:
        raise UniversoIndisponivel(f"índice de sitemap ilegível em {indice}: {erro}") from erro
    nomes = []
    for loc in _texto_locs(conteudo):
        nome = loc.rsplit("/", 1)[-1]
        if nome.endswith(".xml"):
            nomes.append(nome)
    return list(dict.fromkeys(nomes))


def urls_publicas(raiz_projeto: str) -> list[str]:
    """Todas as URLs que o portal ANUNCIA hoje, na ordem do índice, sem duplicata.

    Levanta UniversoIndisponivel se o índice declarar um shard que não existe:
    isso é 404 anunciado ao crawler, e falhar alto é o comportamento certo.
    """
    urls: list[str] = []
    ausentes: list[str] = []
    for nome in shards_declarados(raiz_projeto):
        caminho = os.path.join(raiz_projeto, SHARDS_DIR_REL, nome)
        try:
            with open(caminho, "rb") as fh:
                urls.extend(_texto_locs(fh.read()))
        except FileNotFoundError:
            ausentes.append(nome)
    if ausentes:
        raise UniversoIndisponivel(
            "o índice anuncia shard que não existe no disco (404 para quem o pedir): "
            + ", ".join(ausentes)
        )
    return list(dict.fromkeys(urls))


def caminhos_publicos(raiz_projeto: str, base_url: str = "https://wikijuridica.com.br") -> list[str]:
    """As mesmas URLs, reduzidas ao caminho (`/area/pagina/`)."""
    prefixo = base_url.rstrip("/")
    return [u[len(prefixo):] if u.startswith(prefixo) else u for u in urls_publicas(raiz_projeto)]
