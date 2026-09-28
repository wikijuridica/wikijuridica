#!/usr/bin/env python3
"""Corrige por CAS quatro fatos juridicos vivos do imobiliario-05.

As outras dezoito linhas sao preservadas byte a byte. O modo --dry-run pode
materializar um candidato fora do shard para auditoria local e global.
"""

import argparse
import copy
import datetime
import hashlib
import json
import os
import posixpath
import re
import tempfile
import unicodedata
import urllib.parse


TARGET = "data/editorial/v2_pages/imobiliario-05.jsonl"
EXPECTED_SHA256 = "cfba1f1fad1664866b4ae3d4781e272e0342e82c148217f1e1a39b9daa2f1b6f"
FINAL_SHA256 = "6fcf46992c39a17dc3e783d50fca16594b0e2e8b521ef386e464d259f623bfd8"
VERIFIED_AT = "2026-07-11"

TARGET_INTENTS = {
    "imob-dupla-venda-mesmo-imovel",
    "imob-vendedor-atrasa-documentacao",
    "imob-divida-condominio-omitida-venda",
    "imob-cessao-direitos-hereditarios-imovel",
}

UNTOUCHED_LINE_SHA256 = {
    "imob-inquilino-rescindir-barulho-predio": "bca2498e114b0de65ef05fe3777dccb8a8285418e5ebfa8cfde367d4cc0803ec",
    "imob-fiador-executado-defesas": "32868067f9a5578541e697ff9232131879fb379d2b6ce9ab01907d16198e669c",
    "imob-negociar-aluguel-atrasado-antes-despejo": "ae562f748c81e26f0ec840594d206a5fd60132d6426449ba6351f0e67dc22c18",
    "imob-imovel-alugado-penhorado-leilao": "65521b2fbf32feca202067ee9ebc5bd69114035b63aa01be8fba2d8e09b87701",
    "imob-sublocacao-valor-maior": "d81bac02375861971e57a57b30f7caf2ed350fa73266b8bc579219d040dbbbf8",
    "imob-condominio-negativar-devedor": "f6ffd9a4b7180578526ef58906b31e6e940d796f130fb915f44e5e50b68be959",
    "imob-condominio-cortar-agua-devedor": "35ba52ffe2508deb0e1866b2fe872e2df59d9b3b033d9b7fbada06a4bf7bb188",
    "imob-rateio-obra-luxo-minoria": "732bdbb461346dbc3cae43a26b48209bb25293d21cc29877e6959c1a40bf1ae8",
    "imob-multa-inquilino-cobrada-dono": "adce83c755ba144cc083e65aafff8e8801f79bc1f7e50be0814491b1bc70a078",
    "imob-sindico-nao-cobra-inadimplentes": "355c356a681f9420f66a7d341eaa498adba14fd207145f7a5473c081f6d6735f",
    "imob-indisponibilidade-bens-vendedor": "d7fe031ee4102f43752441fb2ca61d15cbd8d77a97420c0aa858035a95cb69b0",
    "imob-arrematacao-dividas-anteriores": "92cbe5fb6c2adb8bfb73054af21585d9a28cd90b93ce5dd47374f556c91f5c1e",
    "imob-doacao-imovel-revogacao": "c0c850e462b34f5a4c19e2b016a8114795eab32f7d3626af9d0a28c774e6d5fb",
    "imob-exclusividade-corretor-vendi-sozinho": "ecb88857435b1c6dae6e2f7bf811a5a258268f1aafc296d0802796cc36fb7369",
    "imob-gaveta-comprador-nao-paga-banco": "fd94ba8c4e266ab3f2ceef6a6d7fb47335b3d77e8c0901745ef5259c069fb446",
    "imob-ex-companheiro-nao-sai-imovel": "c675f2f0d97e57f8194ca3ba561a0c7a4e44c44cd63fcd85bd6a3a6d0ca8380e",
    "imob-vizinho-construiu-dentro-terreno": "cda91086e4f19a4c68590bfcb5df32cf971177e5e8ebc7045a0338d0b5d7493c",
    "imob-arvore-vizinho-caiu-dano": "d906796fb092241f341a69d6bbb9a99ea850ab44779807d4a5c46fdcd8051e8a",
}

ALLOWED_TOP_LEVEL_CHANGES = {"sections", "faq", "official_sources", "word_count"}


def source(url, name, claim):
    return {
        "url": url,
        "name": name,
        "anchor_claim": claim,
        "verified_at": VERIFIED_AT,
        "http_status": 200,
    }


def find_section(page, heading):
    for item in page.get("sections", []):
        if item.get("heading") == heading:
            return item
    raise RuntimeError(f"{page['intent_id']}: secao ausente: {heading}")


def replace_section(page, old_heading, new_heading, text):
    item = find_section(page, old_heading)
    item["heading"] = new_heading
    item["text"] = text


def rewrite_double_sale(page):
    replace_section(
        page,
        "REsp 2.141.417 é limite de publicidade, não caso de dupla venda",
        "AgInt na AR 5.465: boa-fé registral admite prova em contrário",
        "No AgInt na AR 5.465, o STJ manteve a improcedência da ação rescisória dirigida contra acórdão que havia desconstituído a segunda alienação e as seguintes. "
        "A falta de averbação da primeira promessa gerava presunção relativa de boa-fé em favor do adquirente posterior, não proteção absoluta. Como o tribunal de origem encontrou prova em contrário e afastou a boa-fé, o STJ não refez essa conclusão fática. "
        "O precedente não autoriza cancelar todo registro posterior apenas pela data do primeiro contrato: matrícula, publicidade e prova de má-fé continuam decisivas no caso concreto.",
    )
    replace_section(
        page,
        "Dupla venda não é automaticamente crime",
        "Dupla venda não é automaticamente crime",
        "A existência de dois contratos incompatíveis não é automaticamente crime. O artigo 171, parágrafo 2º, inciso II, do Código Penal alcança, entre outras condutas, a alienação de imóvel que o agente prometeu vender a terceiro mediante pagamento em prestações, quando silencia sobre essa circunstância. "
        "A responsabilização penal exige apuração dos elementos do tipo, inclusive fraude e dolo; controvérsia civil ou falha registral, sozinha, não os demonstra. Boletim de ocorrência não substitui a ação patrimonial nem cancela registro, e a notícia do fato deve ser documental, sem servir como ameaça de cobrança.",
    )
    page["official_sources"] = [
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1245",
            "Código Civil, art. 1.245",
            "faz do registro do título o modo de transferência da propriedade entre vivos",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art167",
            "Lei 6.015/1973, art. 167",
            "classifica a compra e venda entre os atos sujeitos a registro imobiliário",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art182",
            "Lei 6.015/1973, arts. 182 e 186",
            "organiza a prioridade dos títulos pela ordem de apresentação e prenotação",
        ),
        source(
            "https://www.stj.jus.br/websecstj/cgi/revista/REJ.cgi/ITA?dt=20181218&formato=HTML&nreg=201402509840&salvar=false&seq=1784723&tipo=0",
            "STJ, AgInt na AR 5.465/TO",
            "examina dupla alienação, presunção relativa de boa-fé e prova em contrário no caso julgado",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm#art171",
            "Código Penal, art. 171, § 2º, II",
            "tipifica a disposição fraudulenta de coisa própria nas hipóteses legais específicas",
        ),
    ]


def rewrite_seller_documents(page):
    replace_section(
        page,
        "Mora pode nascer do vencimento ou da interpelação",
        "Termo contratual e interpelação definem o início da mora",
        "Pelo artigo 397 do Código Civil, o descumprimento de obrigação positiva, líquida e com termo constitui o devedor em mora de pleno direito. Quando não existe prazo certo, a mora depende de interpelação judicial ou extrajudicial. "
        "A notificação deve relacionar os documentos faltantes, fixar prazo razoável para a entrega e indicar a consequência contratual, sempre com prova de recebimento. Mensagem vaga perguntando se há novidades pode não cumprir a mesma função.",
    )
    replace_section(
        page,
        "Exigência registral pode mostrar que o atraso é sanável",
        "Nota de exigências e prenotação obedecem regras distintas",
        "Se a escritura já foi apresentada, a nota devolutiva, também chamada nota de exigências, deve observar o artigo 198 da Lei de Registros Públicos: o oficial indica por escrito, de uma só vez, articuladamente e de forma clara e objetiva, as exigências necessárias ao registro. Se o interessado não puder cumpri-las ou não concordar, pode requerer que o título e a declaração de dúvida sejam remetidos ao juízo competente. "
        "Outra regra cuida da duração da prioridade: o artigo 205 prevê cessação automática dos efeitos da prenotação depois de vinte dias quando o título não foi registrado por omissão do interessado em atender às exigências legais. A simples discordância ou instauração regular da dúvida não deve ser descrita como perda automática do protocolo. Nota, recibo da prenotação e andamento do procedimento precisam ser examinados em conjunto antes de pagar o saldo ou abandonar o negócio.",
    )
    page["official_sources"] = [
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art397",
            "Código Civil, art. 397",
            "distingue mora de pleno direito no termo e constituição por interpelação quando não há termo",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art475",
            "Código Civil, art. 475",
            "permite exigir cumprimento ou pedir resolução, com perdas e danos cabíveis",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art417",
            "Código Civil, arts. 417 a 420",
            "disciplina as arras conforme a execução, a culpa e eventual direito de arrependimento",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art198",
            "Lei 6.015/1973, art. 198",
            "exige indicação escrita, clara e objetiva das exigências formuladas pelo registro",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art205",
            "Lei 6.015/1973, art. 205",
            "disciplina a cessação da prenotação por omissão no atendimento das exigências legais",
        ),
    ]


def rewrite_hidden_condominium_debt(page):
    replace_section(
        page,
        "Tema 886 está sob revisão no Tema 1.349",
        "Tema 886 permanece vigente enquanto o Tema 1.349 está afetado",
        "O Tema 886 relaciona posse e ciência inequívoca do condomínio à definição do polo passivo na promessa não registrada. Em maio de 2025, o Tema 1.349 foi afetado para revisar essa tese e decidir se existe legitimidade concorrente entre vendedor registral e comprador, independentemente da ciência inequívoca da transação pelo condomínio. "
        "O cadastro determina a suspensão dos recursos especiais e agravos em recurso especial, na segunda instância ou no STJ, que tratem de questão idêntica à discutida no Tema 886. Na consulta oficial atualizada em 10 de fevereiro de 2026, o Tema 1.349 permanecia afetado, sem tese nova julgada. "
        "Por isso, a revisão pendente não deve ser apresentada como superação definitiva do Tema 886. A responsabilidade perante o condomínio e o regresso contratual contra quem omitiu a dívida continuam em planos distintos.",
    )
    replace_section(
        page,
        "Execução em curso exige ingresso defensivo imediato",
        "Execução em curso exige ingresso defensivo imediato",
        "O artigo 784, inciso X, do Código de Processo Civil reconhece como título executivo extrajudicial o crédito de contribuições condominiais documentalmente comprovado. Se a unidade já foi penhorada por cotas anteriores, o novo titular deve obter o processo completo, comprovar a aquisição e verificar citação, saldo e fase da expropriação. "
        "A escritura não encerra a execução automaticamente. A medida processual depende de como o direito foi atingido e de quem integra o polo, podendo envolver defesa do executado, intervenção ou embargos de terceiro. Paralelamente, o vendedor deve ser notificado para assumir ou garantir o passivo conforme prometido.",
    )
    page["official_sources"] = [
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1345",
            "Código Civil, art. 1.345",
            "atribui ao adquirente os débitos condominiais do alienante, inclusive multas e juros",
        ),
        source(
            "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=886&cod_tema_inicial=886&novaConsulta=true&tipo_pesquisa=T",
            "STJ, Tema Repetitivo 886",
            "registra a tese vigente sobre posse, ciência inequívoca e responsabilidade por cotas",
        ),
        source(
            "https://processo.stj.jus.br/repetitivos/temas_repetitivos/pesquisa.jsp?cod_tema_final=1349&cod_tema_inicial=1349&novaConsulta=true&tipo_pesquisa=T",
            "STJ, Tema Repetitivo 1.349",
            "registra a afetação da proposta de revisão do Tema 886 e seu estado ainda não julgado",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art422",
            "Código Civil, art. 422",
            "impõe probidade e boa-fé na execução do contrato de venda",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm#art784",
            "Código de Processo Civil, art. 784, X",
            "reconhece a executividade da contribuição condominial documentalmente comprovada",
        ),
    ]


def rewrite_inheritance_assignment(page):
    replace_section(
        page,
        "Cessão de bem singular da herança é ineficaz",
        "Bem singular: ineficácia não significa nulidade automática",
        "O parágrafo 2º do artigo 1.793 chama de ineficaz a cessão feita pelo coerdeiro sobre bem singular da herança. No REsp 1.809.548, o STJ esclareceu que, celebrada por escritura pública e sem envolver direito de incapaz, essa cessão não é nula nem inválida: há eficácia condicionada à atribuição do bem ao cedente na partilha, e a ineficácia opera perante os demais herdeiros. "
        "Se houver herdeiro único ou anuência de todos os coerdeiros, o precedente reconhece eficácia desde a celebração, sem converter o negócio em registro imediato da propriedade. Situação diferente é a disposição de bem do acervo pelo herdeiro, durante a indivisibilidade, sem prévia autorização do juízo, hipótese tratada no parágrafo 3º.",
    )
    page["faq"] = [
        {
            "q": "Posso ceder somente a casa que imagino receber?",
            "a": "Segundo o REsp 1.809.548, a cessão singular formalizada por escritura pública e sem envolver direito de incapaz não é nula. Em regra, porém, é ineficaz perante coerdeiros que não anuíram e não garante domínio: sua eficácia depende de o bem caber ao cedente na partilha. O precedente ressalva o herdeiro único e a anuência de todos os coerdeiros.",
        },
        {
            "q": "Contrato particular basta para ceder direitos hereditários?",
            "a": "Não. O artigo 1.793 exige escritura pública para a cessão do direito à sucessão aberta ou do quinhão do coerdeiro.",
        },
    ]
    page["official_sources"] = [
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1793",
            "Código Civil, art. 1.793",
            "exige escritura pública e disciplina a ineficácia da cessão referente a bem singular",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1794",
            "Código Civil, art. 1.794",
            "assegura preferência ao coerdeiro na cessão onerosa de quota a estranho",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art1795",
            "Código Civil, art. 1.795",
            "prevê depósito do preço e prazo de cento e oitenta dias para o coerdeiro preterido",
        ),
        source(
            "https://processo.stj.jus.br/jurisprudencia/externo/informativo/?livre=@CNOT=017649",
            "STJ, REsp 1.809.548/SP, Informativo 672",
            "distingue nulidade e ineficácia condicionada da cessão hereditária sobre bem singular",
        ),
        source(
            "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm#art167",
            "Lei 6.015/1973, art. 167",
            "prevê o ingresso registral do título sucessório adequado, como formal de partilha ou adjudicação",
        ),
    ]


UPDATERS = {
    "imob-dupla-venda-mesmo-imovel": rewrite_double_sale,
    "imob-vendedor-atrasa-documentacao": rewrite_seller_documents,
    "imob-divida-condominio-omitida-venda": rewrite_hidden_condominium_debt,
    "imob-cessao-direitos-hereditarios-imovel": rewrite_inheritance_assignment,
}


def deaccent(value):
    return "".join(
        char
        for char in unicodedata.normalize("NFD", value or "")
        if not unicodedata.combining(char)
    )


def count_words(value):
    return len(re.findall(r"[^\W_]+", deaccent(value).lower(), re.UNICODE))


def body_word_count(page):
    total = count_words(page.get("opening", ""))
    for item in page.get("sections", []):
        total += count_words(item.get("heading", ""))
        total += count_words(item.get("text", ""))
    for item in page.get("faq", []):
        total += count_words(item.get("q", ""))
        total += count_words(item.get("a", ""))
    return total


def normalized_source_url(value):
    parsed = urllib.parse.urlsplit((value or "").strip())
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        port = None
    if (scheme == "https" and port == 443) or (scheme == "http" and port == 80):
        port = None
    path = posixpath.normpath(urllib.parse.unquote(parsed.path) or "/")
    if not path.startswith("/"):
        path = "/" + path
    query = urllib.parse.urlencode(
        sorted(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)),
        doseq=True,
    )
    return scheme, host, port, path, query, urllib.parse.unquote(parsed.fragment)


def line_sha(raw_line):
    return hashlib.sha256(raw_line.encode("utf-8")).hexdigest()


def parse_payload(payload):
    records = []
    seen = set()
    for position, raw_line in enumerate(payload.decode("utf-8").splitlines(), 1):
        if not raw_line.strip():
            raise RuntimeError(f"linha vazia inesperada: {position}")
        page = json.loads(raw_line)
        intent = page.get("intent_id")
        if not intent or intent in seen:
            raise RuntimeError(f"intent ausente ou duplicado: {intent}")
        seen.add(intent)
        records.append((raw_line, page))
    if len(records) != 22:
        raise RuntimeError(f"contagem inesperada: {len(records)}")
    if seen != TARGET_INTENTS | set(UNTOUCHED_LINE_SHA256):
        raise RuntimeError("conjunto de intents divergiu do CAS")
    for raw_line, page in records:
        intent = page["intent_id"]
        if intent in UNTOUCHED_LINE_SHA256:
            if line_sha(raw_line) != UNTOUCHED_LINE_SHA256[intent]:
                raise RuntimeError(f"linha fora do escopo alterada: {intent}")
    return records


def validate_target(page):
    intent = page["intent_id"]
    real = body_word_count(page)
    page["word_count"] = real
    if not 630 <= real <= 1540:
        raise RuntimeError(f"{intent}: word_count={real} fora de 630-1540")
    sources = page.get("official_sources", [])
    if not 2 <= len(sources) <= 5:
        raise RuntimeError(f"{intent}: fontes={len(sources)}")
    seen = set()
    for item in sources:
        if not all(
            str(item.get(key, "")).strip()
            for key in ("url", "name", "anchor_claim", "verified_at")
        ):
            raise RuntimeError(f"{intent}: fonte incompleta")
        datetime.date.fromisoformat(item["verified_at"])
        if item.get("http_status") not in {200, 203, 206}:
            raise RuntimeError(f"{intent}: http_status invalido")
        normalized = normalized_source_url(item["url"])
        if normalized in seen:
            raise RuntimeError(f"{intent}: URL de fonte duplicada")
        seen.add(normalized)


def build_output(original):
    rendered = []
    changed = set()
    for raw_line, page in parse_payload(original):
        intent = page["intent_id"]
        if intent not in TARGET_INTENTS:
            rendered.append(raw_line + "\n")
            continue
        before = copy.deepcopy(page)
        UPDATERS[intent](page)
        validate_target(page)
        changed_keys = {
            key for key in set(before) | set(page) if before.get(key) != page.get(key)
        }
        if not changed_keys <= ALLOWED_TOP_LEVEL_CHANGES:
            raise RuntimeError(f"{intent}: campos fora do escopo: {sorted(changed_keys)}")
        changed.add(intent)
        rendered.append(json.dumps(page, ensure_ascii=False, separators=(",", ":")) + "\n")
    if changed != TARGET_INTENTS:
        raise RuntimeError(f"intents nao alteradas: {sorted(TARGET_INTENTS - changed)}")
    output = "".join(rendered).encode("utf-8")
    parse_payload(output)
    return output


def validate_final(payload):
    targets = 0
    for _, page in parse_payload(payload):
        if page["intent_id"] in TARGET_INTENTS:
            validate_target(page)
            targets += 1
    if targets != 4:
        raise RuntimeError(f"paginas alvo finais={targets}")


def atomic_write(path, payload, prefix):
    directory = os.path.dirname(os.path.abspath(path))
    descriptor, temporary = tempfile.mkstemp(prefix=prefix, dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fchmod(handle.fileno(), 0o644)
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--candidate", metavar="PATH")
    args = parser.parse_args()
    if args.dry_run and args.check:
        raise SystemExit("--dry-run e --check sao mutuamente exclusivos")
    if args.candidate and not args.dry_run:
        raise SystemExit("--candidate exige --dry-run")
    if args.candidate and os.path.abspath(args.candidate) == os.path.abspath(TARGET):
        raise SystemExit("--candidate nao pode ser o shard alvo")

    with open(TARGET, "rb") as handle:
        original = handle.read()
    actual = hashlib.sha256(original).hexdigest()

    if args.check:
        if not FINAL_SHA256:
            raise SystemExit("FINAL_SHA256 ainda nao fixado")
        if actual != FINAL_SHA256:
            raise SystemExit(f"check CAS falhou: esperado {FINAL_SHA256}, encontrado {actual}")
        validate_final(original)
        print(f"check=pass targets=4 untouched=18 sha256={actual}")
        return

    if actual != EXPECTED_SHA256:
        raise SystemExit(f"CAS falhou: esperado {EXPECTED_SHA256}, encontrado {actual}")
    output = build_output(original)
    output_sha = hashlib.sha256(output).hexdigest()
    if FINAL_SHA256 and output_sha != FINAL_SHA256:
        raise SystemExit(f"output divergente: esperado {FINAL_SHA256}, encontrado {output_sha}")
    if args.dry_run:
        if args.candidate:
            atomic_write(args.candidate, output, ".imobiliario-05-candidate.")
        print(f"dry_run=pass targets=4 untouched=18 sha256={output_sha}")
        return

    with open(TARGET, "rb") as handle:
        current = hashlib.sha256(handle.read()).hexdigest()
    if current != EXPECTED_SHA256:
        raise SystemExit(f"CAS mudou antes da promocao: {current}")
    atomic_write(TARGET, output, ".imobiliario-05.")
    print(f"promoted=pass targets=4 untouched=18 sha256={output_sha}")


if __name__ == "__main__":
    main()
