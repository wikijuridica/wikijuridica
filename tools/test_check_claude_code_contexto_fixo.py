#!/usr/bin/env python3
"""Prende as reguas de tools/check-claude-code-contexto-fixo com transcripts sinteticos.

Roda: python3 tools/test_check_claude_code_contexto_fixo.py

Cada caso monta um CLAUDE_CONFIG_DIR temporario com transcripts no formato que o CLI
grava (JSON compacto, uma linha por registro, os mesmos tipos e chaves medidos em
~/.claude/projects/-opt-wiki em 2026-09-23) e confere rc + veredito + regra acusada.

Depois vem a prova por mutacao ("teste e aprendizado sao par"): cada regua e cada
decisao de leitura do check e' desligada numa COPIA do codigo, e a suite inteira tem de
reprovar a copia. Mutante que sobrevive denuncia caso faltando, nao check certo:
  M1  agents-md desligada            M8  seleciona `claude -p` (sdk-cli) como interativa
  M2  teto de instrucoes x100        M9  usa o `usage` de topo e ignora `iterations`
  M3  teto de skill_listing x100     M10 le listagens so ate o 1o turno
  M4  nomes `plugin:` ignorados      M11 aceita continuacao pos-compactacao
  M5  prefixo de conector ignorado   M12 fronteira do prompt vira `>=`
  M6  teto do prompt x100            M13 conteudo de instrucao vaza na saida
  M7  teto do `Bash true` 99 s       M14 `nao medido` sai com rc 0
  M15 instrucao injetada de conector ignorada
  M16 conector BLOQUEADO (so' em failedMcpServers) contado como presente — falso vermelho
      exatamente na sessao em que o `deniedMcpServers` funcionou
  M17 linha que nao e' JSON engolida em silencio (sem contagem nem aviso)
  M18 regua `conector` sem nada para ver sai verde calada (sessao que saiu antes do MCP)
  M19 selecao pelo mtime: sessao longa, aberta cedo e ainda escrevendo, esconde a nova
Nenhum caso imprime conteudo de transcript real: tudo e' sintetico.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(RAIZ, "tools", "check-claude-code-contexto-fixo")
SEGREDO = "CONTEUDO-SINTETICO-QUE-NUNCA-PODE-SAIR-7f3a"
SID = "00000000-0000-4000-8000-000000000001"


def linha(obj) -> str:
    """Formato do CLI: JSON.stringify, sem espacos."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def texto(nbytes: int, nlinhas: int) -> str:
    """Conteudo ASCII com nlinhas linhas NAO vazias e exatamente nbytes bytes, com o
    SEGREDO na primeira. Linha vazia no fim seria aparada pela contagem do CLI."""
    linhas = [SEGREDO] + ["l"] * (nlinhas - 1)
    base = len("\n".join(linhas))
    assert base <= nbytes, (nbytes, nlinhas)
    linhas[0] += "a" * (nbytes - base)
    return "\n".join(linhas)


def ts(segundos: float) -> str:
    total_ms = int(round(segundos * 1000))
    s, ms = divmod(total_ms, 1000)
    m, s = divmod(s, 60)
    return f"2026-09-23T10:{m:02d}:{s:02d}.{ms:03d}Z"


def anexo(tipo: str, corpo: dict, t: float, ep: str) -> dict:
    return {"parentUuid": None, "isSidechain": False, "attachment": {"type": tipo, **corpo},
            "type": "attachment", "entrypoint": ep, "timestamp": ts(t), "sessionId": SID}


def listagem_skill(nbytes: int, nomes=("rodar-gate", "caveman:caveman")) -> dict:
    corpo = {"content": "", "isInitial": True, "names": list(nomes), "skillCount": len(nomes)}
    # mesma grandeza do check e dos numeros do plano: json.dumps com separadores padrao
    vazio = len(json.dumps({"type": "skill_listing", **corpo}, ensure_ascii=False).encode())
    corpo["content"] = "s" * max(nbytes - vazio, 0)
    return corpo


INSTRUCOES_LEVES = [
    ("/home/u/.claude/CLAUDE.md", "User", 13_583, 270),
    ("/opt/proj/CLAUDE.md", "Project", 21_436, 271),
    ("/home/u/.claude/projects/-opt-proj/memory/MEMORY.md", "AutoMem", 20_000, 150),
]


def sessao(*, ep="cli", modo="auto", registro_pm=True, instrucoes=INSTRUCOES_LEVES,
           skill_b=14_439, deferred=("Bash", "mcp__context-mode__ctx_search", "mcp__wikijuridica__fetch"),
           mcp_nomes=("wikijuridica",), listagens_depois=False, uso=None, iteracoes=None,
           bash_true=0.2, continuacao=False, com_turno=True, falhos=(), sem_mcp=False,
           t0=0) -> list[str]:
    """t0: segundos somados a todos os timestamps (sessao aberta mais tarde)."""
    reg: list[dict] = [{"type": "last-prompt", "leafUuid": "x", "sessionId": SID}]
    if registro_pm:
        reg.append({"type": "permission-mode", "permissionMode": modo, "sessionId": SID})
    reg.append({"parentUuid": None, "isSidechain": False, "type": "user", "entrypoint": ep,
                "permissionMode": modo, "timestamp": ts(t0), "sessionId": SID,
                "message": {"role": "user", "content": "pedido"}})
    listas = [
        anexo("deferred_tools_delta", {"addedNames": list(deferred), "addedLines": list(deferred),
                                       "removedNames": ["mcp__plugin_velho_x__y"], "pendingMcpServers": [],
                                       "failedMcpServers": [{"name": n, "error": "blocked by policy"}
                                                            for n in falhos]}, t0 + 1, ep),
        anexo("agent_listing_delta", {"addedTypes": ["investigador"], "addedLines": ["- investigador"],
                                      "isInitial": True, "removedTypes": []}, t0 + 1, ep),
        anexo("mcp_instructions_delta", {"addedNames": list(mcp_nomes), "addedBlocks": ["## bloco"],
                                         "removedNames": []}, t0 + 1, ep),
        anexo("skill_listing", listagem_skill(skill_b), t0 + 1, ep),
    ]
    if sem_mcp:
        # sessao que sai antes de qualquer servidor MCP conectar (medido em 2026-09-23:
        # quatro sessoes de 3 a 10 s): nenhum mcp_instructions_delta no arquivo
        listas = [a for a in listas if a["attachment"]["type"] != "mcp_instructions_delta"]
    if not listagens_depois:
        reg.extend(listas)
    if instrucoes is not None:
        reg.append(anexo("instructions", {"files": [
            {"path": p, "type": tp, "content": texto(nb, nl)} for p, tp, nb, nl in instrucoes]}, t0 + 2, ep))
    if continuacao:
        reg.append({"parentUuid": None, "isSidechain": False, "type": "user", "entrypoint": ep,
                    "isCompactSummary": True, "timestamp": ts(t0 + 2), "sessionId": SID,
                    "message": {"role": "user", "content": "resumo"}})
    if com_turno:
        u = uso if uso is not None else {"input_tokens": 2, "cache_creation_input_tokens": 70_000,
                                         "cache_read_input_tokens": 9_000, "output_tokens": 10}
        if iteracoes is not None:
            u = dict(u, iterations=iteracoes)
        conteudo = [{"type": "text", "text": "ok"}]
        if bash_true is not None:
            conteudo.append({"type": "tool_use", "id": "toolu_true1", "name": "Bash",
                             "input": {"command": "true", "description": "sonda"}})
        reg.append({"parentUuid": None, "isSidechain": False, "type": "assistant", "entrypoint": ep,
                    "timestamp": ts(t0 + 5), "sessionId": SID,
                    "message": {"model": "claude-opus-5-5", "id": "msg_1", "role": "assistant",
                                "content": conteudo, "usage": u}})
        if bash_true is not None:
            reg.append({"parentUuid": None, "isSidechain": False, "type": "user", "entrypoint": ep,
                        "timestamp": ts(t0 + 5 + bash_true), "sessionId": SID,
                        "message": {"role": "user", "content": [
                            {"type": "tool_result", "tool_use_id": "toolu_true1", "content": ""}]}})
    if listagens_depois:
        reg.extend(listas)
    return [linha(r) for r in reg]


class Ambiente:
    def __init__(self, raiz: str):
        self.cfg = os.path.join(raiz, "cfg")
        self.projeto = os.path.join(raiz, "proj")
        self.dir = os.path.join(self.cfg, "projects", self.projeto.replace("/", "-"))
        os.makedirs(os.path.join(self.dir, "memory"), exist_ok=True)
        self.memoria(150, 20_000)
        self.n = 0

    def memoria(self, nlinhas: int, nbytes: int):
        with open(os.path.join(self.dir, "memory", "MEMORY.md"), "w") as fh:
            fh.write(texto(nbytes, nlinhas))

    def grava(self, linhas: list[str], idade_s: int = 0) -> str:
        self.n += 1
        caminho = os.path.join(self.dir, f"sessao-{self.n:02d}.jsonl")
        with open(caminho, "w", encoding="utf-8") as fh:
            fh.write("\n".join(linhas) + "\n")
        instante = 1_790_000_000 - idade_s
        os.utime(caminho, (instante, instante))
        return caminho

    def roda(self, script: str, *args: str):
        env = dict(os.environ, CLAUDE_CONFIG_DIR=self.cfg)
        p = subprocess.run([sys.executable, script, "--projeto", self.projeto, *args],
                           capture_output=True, text=True, env=env, timeout=60)
        try:
            dados = json.loads(p.stdout)
        except json.JSONDecodeError:
            dados = {}
        return p.returncode, dados, p.stdout + p.stderr


def acusa(dados: dict, regra: str) -> bool:
    return any(v.startswith(regra + ":") for v in dados.get("violacoes", []))


def suite(script: str, verboso: bool) -> list[str]:
    """Todos os diretorios temporarios da rodada ficam sob UM TemporaryDirectory, que o
    `with` apaga: a bancada diaria roda isto 15 vezes (suite + 14 mutantes) por dia."""
    with tempfile.TemporaryDirectory(prefix="ctxfixo-") as raiz_tmp:
        return _suite(script, verboso, raiz_tmp)


def _suite(script: str, verboso: bool, raiz_tmp: str) -> list[str]:
    falhas: list[str] = []

    def caso(nome: str, ok: bool, detalhe: str = ""):
        if verboso:
            print(f"  {'ok ' if ok else 'ERRO'} {nome} {detalhe}")
        if not ok:
            falhas.append(nome)

    def isolado(**kw):
        tmp = tempfile.mkdtemp(dir=raiz_tmp)
        amb = Ambiente(tmp)
        caminho = amb.grava(sessao(**kw))
        return amb, caminho

    # 1. sessao enxuta: verde, sem aviso de memoria nem de modo
    amb, c = isolado()
    rc, d, out = amb.roda(script, "--transcript", c)
    caso("sessao enxuta passa", rc == 0 and d.get("veredito") == "verde" and not d.get("violacoes"), f"rc={rc}")
    caso("sessao enxuta sem aviso de memoria/modo",
         not any(a.startswith(("memoria", "permission-mode")) for a in d.get("avisos", [])), str(d.get("avisos")))
    caso("prompt_total = input + cache_creation + cache_read",
         (d.get("primeiro_turno") or {}).get("prompt_total") == 79_002, str(d.get("primeiro_turno")))
    caso("conteudo de instrucao nunca sai na saida", SEGREDO not in out)

    # 2. AGENTS.md no anexo
    amb, c = isolado(instrucoes=INSTRUCOES_LEVES[:2] + [("/opt/proj/AGENTS.md", "Project", 3_000, 10)])
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("AGENTS.md reprova mesmo com instrucoes abaixo do teto", rc == 1 and acusa(d, "agents-md")
         and not acusa(d, "instrucoes"), f"rc={rc} {d.get('violacoes')}")

    # 3. teto de instrucoes: 62.000 passa, 62.001 reprova (o porque do 62.000 esta no check)
    for total, esperado in ((62_000, 0), (62_001, 1)):
        base = 13_583 + 21_436
        amb, c = isolado(instrucoes=INSTRUCOES_LEVES[:2] + [
            ("/home/u/.claude/projects/-opt-proj/memory/MEMORY.md", "AutoMem", total - base, 150)])
        rc, d, _ = amb.roda(script, "--transcript", c)
        caso(f"instrucoes {total} B -> rc {esperado}", rc == esperado and acusa(d, "instrucoes") == bool(esperado),
             f"rc={rc} total={(d.get('instrucoes') or {}).get('total_bytes')}")

    # 4. skill_listing: 20.000 passa, 20.001 reprova
    for tamanho, esperado in ((20_000, 0), (20_001, 1)):
        amb, c = isolado(skill_b=tamanho)
        rc, d, _ = amb.roda(script, "--transcript", c)
        medido = ((d.get("listagens") or {}).get("skill_listing") or {}).get("max_bytes")
        caso(f"skill_listing {tamanho} B -> rc {esperado}", rc == esperado and medido == tamanho, f"rc={rc} medido={medido}")

    # 5. plugin: servidor `plugin:` nas instrucoes de MCP e ferramenta `mcp__plugin_` no deferred
    amb, c = isolado(mcp_nomes=("wikijuridica", "plugin:healthcare:NPI Registry"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("servidor plugin: reprova", rc == 1 and acusa(d, "plugin"), f"rc={rc}")
    amb, c = isolado(deferred=("Bash", "mcp__plugin_bio-research_chembl__drug_search"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("ferramenta mcp__plugin_ reprova", rc == 1 and acusa(d, "plugin"), f"rc={rc}")

    # 6. conector claude.ai barrado; legitimos (caveman, context-mode, wikijuridica, GSC) passam
    amb, c = isolado(deferred=("Bash", "mcp__claude_ai_Harvey__authenticate"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("conector claude.ai Harvey reprova", rc == 1 and acusa(d, "conector"), f"rc={rc}")
    amb, c = isolado(deferred=("mcp__context-mode__ctx_search", "mcp__wikijuridica__fetch",
                               "mcp__claude_ai_Advanced_GSC__query"), mcp_nomes=("wikijuridica", "claude.ai Advanced GSC"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("nomes legitimos nao reprovam (falso positivo)", rc == 0, f"rc={rc} {d.get('violacoes')}")
    amb, c = isolado(mcp_nomes=("wikijuridica", "claude.ai Claude Docs"), deferred=("Bash",))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("instrucoes injetadas do conector barrado reprovam", rc == 1 and acusa(d, "conector"), f"rc={rc}")
    amb, c = isolado(falhos=("claude.ai Claude Docs", "claude.ai 中央社 CNA", "claude.ai Harvey"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("conector BLOQUEADO (so' em failedMcpServers) nao reprova", rc == 0, f"rc={rc} {d.get('violacoes')}")
    amb, c = isolado(falhos=("plugin:cockroachdb:cockroachdb-toolbox",))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("servidor plugin: que falhou ainda reprova (sincronizacao ligada)", rc == 1 and acusa(d, "plugin"), f"rc={rc}")

    # 6b. regua `conector` sem nada para ver: aviso, nunca verde calado nem vermelho
    amb, c = isolado(sem_mcp=True, deferred=("Bash",))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("sem MCP conectado: conector nao medido vira aviso (rc 0)",
         rc == 0 and any(a.startswith("conector:") and "nao medida" in a for a in d.get("avisos", [])),
         f"rc={rc} {d.get('avisos')}")
    amb, c = isolado()
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("com MCP conectado: sem aviso de conector", rc == 0
         and not any(a.startswith("conector:") for a in d.get("avisos", [])), f"rc={rc} {d.get('avisos')}")
    amb, c = isolado(sem_mcp=True, deferred=("Bash", "mcp__claude_ai_Advanced_GSC__query"))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("servidor claude.ai visto sem instrucoes: sem aviso de conector", rc == 0
         and not any(a.startswith("conector:") for a in d.get("avisos", [])), f"rc={rc} {d.get('avisos')}")

    # 7. prompt_total: 82.000 passa, 82.001 reprova
    for total, esperado in ((82_000, 0), (82_001, 1)):
        amb, c = isolado(uso={"input_tokens": 1, "cache_creation_input_tokens": total - 1, "cache_read_input_tokens": 0})
        rc, d, _ = amb.roda(script, "--transcript", c)
        caso(f"prompt_total {total} -> rc {esperado}", rc == esperado and acusa(d, "prompt") == bool(esperado), f"rc={rc}")

    # 8. uso de topo zerado com iteracoes (medido em b1a3c454): vale a iteracao `message`
    amb, c = isolado(uso={"input_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
                     iteracoes=[{"type": "message", "input_tokens": 2, "cache_creation_input_tokens": 90_000,
                                 "cache_read_input_tokens": 0},
                                {"type": "advisor_message", "input_tokens": 500_000}])
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("uso zerado no topo: prompt vem de iterations[message]", rc == 1 and acusa(d, "prompt")
         and (d.get("primeiro_turno") or {}).get("prompt_total") == 90_002, f"rc={rc}")

    # 9. Bash true: 0,5 s passa, 0,6 s reprova; ausente vira aviso
    for atraso, esperado in ((0.5, 0), (0.6, 1)):
        amb, c = isolado(bash_true=atraso)
        rc, d, _ = amb.roda(script, "--transcript", c)
        caso(f"Bash true {atraso} s -> rc {esperado}", rc == esperado and acusa(d, "bash-true") == bool(esperado),
             f"rc={rc} {d.get('bash_true_s')}")
    amb, c = isolado(bash_true=None)
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("sem Bash true: verde com aviso", rc == 0 and any(a.startswith("bash-true") for a in d.get("avisos", [])), f"rc={rc}")

    # 10. listagens que chegam DEPOIS do 1o turno (medido em 011803b3) contam
    amb, c = isolado(listagens_depois=True, mcp_nomes=("plugin:x:y",))
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("listagem depois do 1o turno ainda reprova", rc == 1 and acusa(d, "plugin"), f"rc={rc}")

    # 11. MEMORY.md: aviso, nunca falha
    amb, c = isolado()
    amb.memoria(181, 20_000)
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("MEMORY.md 181 linhas: aviso com rc 0", rc == 0 and any(a.startswith("memoria (disco)") for a in d.get("avisos", [])), f"rc={rc}")
    amb.memoria(150, 24_001)
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("MEMORY.md 24.001 B: aviso com rc 0", rc == 0 and any(a.startswith("memoria (disco)") for a in d.get("avisos", [])), f"rc={rc}")

    # 12. modo inicial != auto: aviso
    amb, c = isolado(modo="default")
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("permission-mode default: aviso com rc 0", rc == 0 and d.get("permission_mode_inicial") == "default"
         and any(a.startswith("permission-mode") for a in d.get("avisos", [])), f"rc={rc}")

    # 13. selecao padrao: o `claude -p` mais novo (pequeno, passaria) e' PULADO, e a
    #     sessao interativa mais velha, que reprova, e' a medida (refutacao 2, item 23)
    tmp = tempfile.mkdtemp(dir=raiz_tmp)
    amb = Ambiente(tmp)
    ruim = amb.grava(sessao(skill_b=60_610), idade_s=600)
    amb.grava(sessao(ep="sdk-cli", registro_pm=False, uso={"input_tokens": 5, "cache_creation_input_tokens": 4_000,
                                                           "cache_read_input_tokens": 0}), idade_s=10)
    amb.grava(sessao(com_turno=False), idade_s=5)
    amb.grava(sessao(continuacao=True), idade_s=1)
    rc, d, _ = amb.roda(script)
    motivos = [p.get("motivo", "") for p in (d.get("selecao") or {}).get("pulados", [])]
    caso("selecao pula claude -p, sessao sem turno e continuacao",
         rc == 1 and d.get("transcript") == ruim and len(motivos) == 3
         and any("sdk-cli" in m for m in motivos) and any("continuacao" in m for m in motivos), f"rc={rc} {motivos}")

    # 13b. sessao LONGA aberta cedo e ainda escrevendo (mtime mais novo) nao esconde a
    #      sessao aberta depois (medido em 2026-09-23: 70ce5aa4 escondia seis sessoes novas)
    tmp = tempfile.mkdtemp(dir=raiz_tmp)
    amb = Ambiente(tmp)
    nova = amb.grava(sessao(t0=1800), idade_s=300)
    amb.grava(sessao(skill_b=60_610, t0=0), idade_s=0)
    rc, d, _ = amb.roda(script)
    caso("selecao pela abertura da sessao, nao pelo mtime", rc == 0 and d.get("transcript") == nova,
         f"rc={rc} escolhido={os.path.basename(d.get('transcript') or '')}")

    # 14. transcript explicito que nao serve: rc 2, nunca 0
    for nome, kw in (("claude -p", dict(ep="sdk-cli", registro_pm=False)),
                     ("continuacao", dict(continuacao=True)),
                     ("sem instrucoes", dict(instrucoes=None)),
                     ("sem 1o turno", dict(com_turno=False))):
        amb, c = isolado(**kw)
        rc, d, _ = amb.roda(script, "--transcript", c)
        caso(f"--transcript {nome}: rc 2 nao medido", rc == 2 and d.get("veredito") == "nao_medido", f"rc={rc}")

    # 15. diretorio sem transcript interativo: rc 2
    tmp = tempfile.mkdtemp(dir=raiz_tmp)
    amb = Ambiente(tmp)
    amb.grava(sessao(ep="sdk-cli", registro_pm=False))
    rc, d, _ = amb.roda(script)
    caso("sem sessao interativa no diretorio: rc 2", rc == 2, f"rc={rc}")

    # 16. ultima linha cortada que o check PRECISAVA ler (a sessao ainda escreve): contada e
    #     avisada, nunca engolida. Linha que nenhum prefiltro seleciona nao e' lida nem contada.
    amb, c = isolado()
    with open(c, "a", encoding="utf-8") as fh:
        fh.write('{"type":"permission-mode","permissionMode":"au')
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("linha cortada: rc 0, contada e avisada", rc == 0 and d.get("linhas_ilegiveis") == 1
         and any(a.startswith("transcript:") for a in d.get("avisos", [])), f"rc={rc} {d.get('linhas_ilegiveis')}")

    # 17. JSON com espacos (formato que o CLI NAO grava): falha fechada, rc 2
    amb, c = isolado()
    with open(c, encoding="utf-8") as fh:
        espaçado = [json.dumps(json.loads(x)) for x in fh.read().splitlines()]
    with open(c, "w", encoding="utf-8") as fh:
        fh.write("\n".join(espaçado) + "\n")
    rc, d, _ = amb.roda(script, "--transcript", c)
    caso("formato inesperado falha fechado (rc 2)", rc == 2, f"rc={rc}")
    return falhas


MUTANTES = [
    ("M1 agents-md", "if agentes_md:", "if False:"),
    ("M2 instrucoes", "if total > TETO_INSTRUCOES_B:", "if total > TETO_INSTRUCOES_B * 100:"),
    ("M3 skills", "if skills > TETO_SKILL_LISTING_B:", "if skills > TETO_SKILL_LISTING_B * 100:"),
    ("M4 plugin", "if RE_PLUGIN.search(nome):", "if False:"),
    ("M5 conector por prefixo", "if origem == \"injetado\" and RE_CONECTOR.search(nome):", "if False:"),
    ("M15 conector por instrucao injetada", "and RE_CONECTOR_NOME.search(nome)):", "and False):"),
    ("M16 conta servidor bloqueado como conector", "if origem == \"injetado\" and RE_CONECTOR.search(nome):",
     "if RE_CONECTOR.search(nome) or RE_CONECTOR_NOME.search(nome):"),
    ("M6 prompt", "if total_prompt > TETO_PROMPT_TOTAL:", "if total_prompt > TETO_PROMPT_TOTAL * 100:"),
    ("M7 bash-true", "lentos = [s for s in med[\"bash_true_s\"] if s > TETO_BASH_TRUE_S]",
     "lentos = [s for s in med[\"bash_true_s\"] if s > 99]"),
    ("M8 sdk-cli como interativa", "if ep.startswith(\"sdk-\") or not info[\"permission_mode\"]:", "if False:"),
    ("M9 ignora iterations", "if isinstance(iteracoes, list):", "if False:"),
    ("M10 listagem so ate o 1o turno", "                elif tipo in LISTAGENS:",
     "                elif tipo in LISTAGENS and r[\"primeiro_turno\"] is None:"),
    ("M11 aceita continuacao", "    if info[\"continuacao\"]:\n        return \"continuacao pos-compactacao\"",
     "    if False:\n        return \"continuacao pos-compactacao\""),
    ("M12 fronteira do prompt", "if total_prompt > TETO_PROMPT_TOTAL:", "if total_prompt >= TETO_PROMPT_TOTAL:"),
    ("M13 vaza conteudo", "\"bytes\": len(conteudo.encode(\"utf-8\")),",
     "\"bytes\": len(conteudo.encode(\"utf-8\")), \"amostra\": conteudo[:80],"),
    ("M17 linha ilegivel engolida em silencio", "ilegiveis[0] += 1", "ilegiveis[0] += 0"),
    ("M19 selecao pelo mtime", "key=lambda t: (t[0], t[1])", "key=lambda t: t[1]"),
    ("M18 conector nao medido sem aviso", "and med[\"listagens\"][\"mcp_instructions_delta\"][\"n\"] == 0):",
     "and False):"),
    ("M14 nao medido com rc 0", "return encerra(\"nao_medido\", 2, f\"transcript nao serve: {recusa}\")",
     "return encerra(\"nao_medido\", 0, f\"transcript nao serve: {recusa}\")"),
]


def main() -> int:
    print("suite contra o check real:")
    falhas = suite(CHECK, verboso=True)
    if falhas:
        print(f"FALHOU: {len(falhas)} caso(s) contra o check real: {falhas}")
        return 1
    fonte = open(CHECK, encoding="utf-8").read()
    sobreviventes = []
    print("prova por mutacao:")
    with tempfile.TemporaryDirectory(prefix="ctxfixo-mut-") as tmp:
        for nome, antigo, novo in MUTANTES:
            if fonte.count(antigo) != 1:
                print(f"  ERRO {nome}: trecho alvo aparece {fonte.count(antigo)} vez(es) no check — mutante nao aplicado")
                sobreviventes.append(nome)
                continue
            caminho = os.path.join(tmp, "mutante.py")
            with open(caminho, "w", encoding="utf-8") as fh:
                fh.write(fonte.replace(antigo, novo))
            mortos_por = suite(caminho, verboso=False)
            print(f"  {'ok ' if mortos_por else 'VIVO'} {nome}: {len(mortos_por)} caso(s) reprovaram"
                  + (f" (ex. {mortos_por[0]})" if mortos_por else ""))
            if not mortos_por:
                sobreviventes.append(nome)
    if sobreviventes:
        print(f"FALHOU: mutante(s) vivo(s): {sobreviventes}")
        return 1
    print(f"OK: suite verde e {len(MUTANTES)} mutantes mortos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
