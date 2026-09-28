#!/usr/bin/env python3
"""Bancada de block-agent-haiku.sh.

Ordem do dono, 2026-09-22: "Haiku é proibido", e "sonnet 5 somente para ganhar contexto". A
guarda confere o modelo EFETIVO do subagente, na ordem que a documentação oficial fixa
(parâmetro da chamada → frontmatter → variável → sessão), porque barrar só a palavra no
parâmetro deixaria passar o caso que de fato aconteceu: o `investigador` rodando Haiku pelo
frontmatter, sem ninguém pedir. Pela mesma ordem, Sonnet só roda em agente que não edita: os de
contexto, sob a guarda de escrita, ou agente com `tools:` só de leitura.

O controle negativo pesa igual: a guarda roda em toda chamada Agent do repositório, e barrar Opus,
Fable ou o Sonnet dos agentes de contexto seria barrar a própria orquestração.

Rodar:  python3 .claude/hooks/block-agent-haiku.test.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "block-agent-haiku.sh"

AGENTES_DO_PROJETO = {
    "leitor-barato.md": "---\nname: leitor-barato\ndescription: fixture\nmodel: haiku\n---\ncorpo\n",
    "leitor-aspas.md": "---\nname: leitor-aspas\ndescription: fixture\nmodel: \"claude-haiku-4-5\" # id completo\n---\n",
    "engenheiro-go.md": "---\nname: engenheiro-go\ndescription: fixture\ntools: Read, Edit, Write, Grep, Glob, Bash\nmodel: opus\neffort: high\n---\n",
    "sem-modelo.md": "---\nname: sem-modelo\ndescription: fixture\ntools: Read\n---\n",
    "herdeiro.md": "---\nname: herdeiro\ndescription: fixture\nmodel: inherit\n---\n",
    "sobreposto.md": "---\nname: sobreposto\ndescription: projeto vence usuário\nmodel: opus\n---\n",
    "nome-diferente-do-arquivo.md": "---\nname: outro-nome\ndescription: o nome vale, não o arquivo\nmodel: HAIKU\n---\n",
    # Formas difíceis do frontmatter, medidas contra o red team de 2026-09-22 (RT-B 6). BOM REAL
    # (bytes EF BB BF, não a mojibake do harness), escalar em bloco, linha vazia antes, CRLF,
    # descrição foldada, TAB no lugar do espaço, e model depois de um bloco aninhado.
    "bom-real.md": "﻿---\nname: bom-real\ndescription: x\nmodel: haiku\n---\n",
    "model-bloco.md": "---\nname: model-bloco\ndescription: x\nmodel:\n  haiku\n---\n",
    "linha-vazia-antes.md": "\n---\nname: linha-vazia-antes\ndescription: x\nmodel: haiku\n---\n",
    "crlf.md": "---\r\nname: crlf\r\ndescription: x\r\nmodel: haiku\r\n---\r\n",
    "desc-folded.md": "---\nname: desc-folded\ndescription: >\n  x longo\nmodel: haiku\n---\n",
    "model-tab.md": "---\nname: model-tab\ndescription: x\nmodel:\thaiku\n---\n",
    "model-apos-hooks.md": "---\nname: model-apos-hooks\ndescription: x\nhooks:\n  PreToolUse:\n    - matcher: Bash\nmodel: haiku\n---\n",
    # Os dois de contexto, como no roster real: Bash, memória e (no documentador) Write — guardados.
    "investigador.md": "---\nname: investigador\ndescription: fixture\ntools: Read, Grep, Glob, Bash, WebFetch, WebSearch\ndisallowedTools: Edit, Write\nmodel: sonnet\neffort: medium\nmemory: project\n---\n",
    "documentador-de-contexto.md": "---\nname: documentador-de-contexto\ndescription: fixture\ntools: Read, Grep, Glob, Bash, Write, WebFetch, WebSearch\nmodel: sonnet\nmemory: project\n---\n",
    # Sonnet fora da guarda: passa só quem não tem como gravar.
    "leitor-puro.md": "---\nname: leitor-puro\ndescription: fixture\ntools: Read, Grep, Glob, WebFetch, WebSearch\nmodel: sonnet\n---\n",
    "leitor-lista.md": "---\nname: leitor-lista\ndescription: fixture\ntools:\n  - Read\n  - \"Grep\"\nmodel: claude-sonnet-5\n---\n",
    "leitor-negado.md": "---\nname: leitor-negado\ndescription: fixture\ntools: Read, Bash\ndisallowedTools: Bash\nmodel: sonnet\n---\n",
    "editor-sonnet.md": "---\nname: editor-sonnet\ndescription: fixture\ntools: Read, Edit\nmodel: sonnet\n---\n",
    "sonnet-sem-tools.md": "---\nname: sonnet-sem-tools\ndescription: herda todas\nmodel: sonnet\n---\n",
    "sonnet-com-bash.md": "---\nname: sonnet-com-bash\ndescription: fixture\ntools: [Read, \"Bash(git log:*)\"]\nmodel: SONNET\n---\n",
    "sonnet-com-memoria.md": "---\nname: sonnet-com-memoria\ndescription: fixture\ntools: Read, Grep\nmodel: sonnet\nmemory: project\n---\n",
    "sonnet-com-mcp.md": "---\nname: sonnet-com-mcp\ndescription: fixture\ntools: Read\nmodel: sonnet\nmcpServers:\n  arquivos:\n    command: servidor-que-grava\n---\n",
    "sonnet-lista-edit.md": "---\nname: sonnet-lista-edit\ndescription: fixture\ntools:\n  - Read\n  - Edit\nmodel: sonnet\n---\n",
}
AGENTES_DO_USUARIO = {
    "so-do-usuario.md": "---\nname: so-do-usuario\ndescription: fixture\nmodel: haiku\n---\n",
    "sobreposto.md": "---\nname: sobreposto\ndescription: perde para o de projeto\nmodel: haiku\n---\n",
}


class Bancada(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="guarda-haiku-")
        cls.raiz = Path(cls._tmp.name) / "wiki"
        cls.home = Path(cls._tmp.name) / "home"
        for base, agentes in ((cls.raiz, AGENTES_DO_PROJETO), (cls.home, AGENTES_DO_USUARIO)):
            pasta = base / ".claude" / "agents"
            pasta.mkdir(parents=True)
            for nome, texto in agentes.items():
                (pasta / nome).write_text(texto, encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def roda(self, entrada: dict | None = None, ferramenta: str = "Agent", bruto: str | None = None,
             env_extra: dict | None = None, path: str = "/usr/bin:/bin", hook: Path = HOOK) -> subprocess.CompletedProcess:
        payload = {"session_id": "bancada", "cwd": str(self.raiz), "hook_event_name": "PreToolUse",
                   "tool_name": ferramenta, "tool_input": entrada or {}}
        env = {"PATH": path, "HOME": str(self.home), "CLAUDE_PROJECT_DIR": str(self.raiz)}
        env.update(env_extra or {})
        return subprocess.run(["bash", str(hook)], input=bruto if bruto is not None else json.dumps(payload),
                              capture_output=True, text=True, cwd=str(self.raiz), env=env, timeout=20)

    def barra(self, entrada: dict, **kw) -> subprocess.CompletedProcess:
        p = self.roda(entrada, **kw)
        self.assertEqual(p.returncode, 2, f"deveria barrar e passou: {entrada} {kw}\nstderr={p.stderr}")
        return p

    def passa(self, entrada: dict, **kw) -> subprocess.CompletedProcess:
        p = self.roda(entrada, **kw)
        self.assertEqual(p.returncode, 0, f"deveria passar e barrou: {entrada} {kw}\nstderr={p.stderr}")
        return p

    def sem_python(self) -> str:
        vazio = Path(self._tmp.name) / "bin-sem-python"
        vazio.mkdir(exist_ok=True)
        for ferramenta in ("cat", "bash", "dirname"):
            destino = vazio / ferramenta
            origem = Path("/bin") / ferramenta if (Path("/bin") / ferramenta).exists() else Path("/usr/bin") / ferramenta
            if not destino.exists():
                destino.symlink_to(origem)
        return str(vazio)


def chamada(tipo: str = "general-purpose", modelo: str | None = None) -> dict:
    entrada = {"description": "tarefa", "prompt": "faça", "subagent_type": tipo}
    if modelo is not None:
        entrada["model"] = modelo
    return entrada


class TesteBarra(Bancada):
    def test_parametro_haiku_em_qualquer_caixa_e_id_completo(self):
        for modelo in ("haiku", "HAIKU", "Haiku", "claude-haiku-4-5-20251001", "claude-haiku-4-5", " haiku "):
            with self.subTest(modelo=modelo):
                self.barra(chamada(modelo=modelo))

    def test_haiku_barra_mesmo_em_agente_de_contexto_e_com_alias_redirecionado(self):
        """A ordem proíbe o nome: ANTHROPIC_DEFAULT_HAIKU_MODEL apontando para Sonnet não o libera."""
        self.barra(chamada("investigador", "haiku"))
        self.barra(chamada(modelo="haiku"), env_extra={"ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-5"})

    def test_parametro_vence_definicao_opus(self):
        self.barra(chamada("engenheiro-go", "haiku"))

    def test_frontmatter_do_projeto_declara_haiku(self):
        """O caso que de fato aconteceu: ninguém pediu Haiku, o frontmatter pedia."""
        self.barra(chamada("leitor-barato"))

    def test_frontmatter_com_aspas_comentario_e_id_completo(self):
        self.barra(chamada("leitor-aspas"))

    def test_nome_do_frontmatter_vale_nao_o_nome_do_arquivo(self):
        self.barra(chamada("outro-nome"))

    def test_agente_de_usuario_sem_homonimo_no_projeto(self):
        self.barra(chamada("so-do-usuario"))

    def test_frontmatter_em_forma_dificil_ainda_resolve_haiku(self):
        """RT-B 6, medido em 2026-09-22: cada forma abaixo escondia o `model: haiku` do leitor
        ingênuo. BOM real (não a mojibake do harness), escalar em bloco, linha vazia antes do
        frontmatter, CRLF, descrição foldada, TAB e model depois de um bloco aninhado."""
        for tipo in ("bom-real", "model-bloco", "linha-vazia-antes", "crlf", "desc-folded",
                     "model-tab", "model-apos-hooks"):
            with self.subTest(tipo=tipo):
                self.barra(chamada(tipo))

    def test_embutido_claude_code_guide_roda_em_haiku(self):
        """Tabela oficial dos embutidos: claude-code-guide → Haiku."""
        self.barra(chamada("claude-code-guide"))

    def test_variavel_para_agente_sem_modelo(self):
        self.barra(chamada("general-purpose"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"})
        self.barra(chamada("sem-modelo"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "claude-haiku-4-5"})

    def test_variavel_forcada_vence_tudo(self):
        self.barra(chamada("engenheiro-go", "opus"),
                   env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "haiku", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": "1"})

    def test_alias_remapeado_para_haiku(self):
        self.barra(chamada("investigador", "sonnet"), env_extra={"ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-haiku-4-5"})
        self.barra(chamada(modelo="opus"), env_extra={"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-haiku-4-5"})

    def test_nome_legado_task(self):
        """Até a v2.1.63 a ferramenta se chamava Task, e o alias ainda vale."""
        self.barra(chamada(modelo="haiku"), ferramenta="Task")

    def test_sem_python_ainda_confere_o_parametro(self):
        self.barra(chamada(modelo="haiku"), path=self.sem_python())

    def test_sem_cat_no_path_ainda_le_o_payload(self):
        """Medido pelo red team de 2026-09-22: com um PATH sem `cat`, o antigo `$(cat)` voltava
        vazio e o hook saía 0. A leitura por `read` embutido do bash não depende de processo."""
        so_bash = Path(self._tmp.name) / "bin-so-bash"
        so_bash.mkdir(exist_ok=True)
        destino = so_bash / "bash"
        if not destino.exists():
            origem = Path("/bin/bash") if Path("/bin/bash").exists() else Path("/usr/bin/bash")
            destino.symlink_to(origem)
        self.barra(chamada(modelo="haiku"), path=str(so_bash))


class TesteSonnetSoEmQuemNaoEdita(Bancada):
    """Ordem do dono, 2026-09-22: Sonnet 5 só colhe contexto e não edita arquivo versionado."""

    def test_parametro_sonnet_em_embutido_que_edita(self):
        for tipo in ("general-purpose", "claude", "fork", "Explore", "Plan", "statusline-setup", "claude-code-guide"):
            with self.subTest(tipo=tipo):
                self.barra(chamada(tipo, "sonnet"))

    def test_parametro_sonnet_em_qualquer_grafia(self):
        for modelo in ("sonnet", "SONNET", "claude-sonnet-5", "sonnet[1m]"):
            with self.subTest(modelo=modelo):
                self.barra(chamada(modelo=modelo))

    def test_parametro_sonnet_vence_definicao_opus(self):
        self.barra(chamada("engenheiro-go", "sonnet"))

    def test_frontmatter_sonnet_com_escrita_bash_memoria_mcp_ou_sem_tools(self):
        for tipo in ("editor-sonnet", "sonnet-lista-edit", "sonnet-sem-tools", "sonnet-com-bash",
                     "sonnet-com-memoria", "sonnet-com-mcp"):
            with self.subTest(tipo=tipo):
                self.barra(chamada(tipo))

    def test_embutido_que_ja_roda_em_sonnet(self):
        """statusline-setup roda em Sonnet pela tabela oficial e edita o settings do usuário."""
        self.barra(chamada("statusline-setup"))

    def test_variavel_sonnet_para_agente_sem_modelo(self):
        self.barra(chamada("general-purpose"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"})

    def test_alias_remapeado_para_sonnet(self):
        self.barra(chamada(modelo="opus"), env_extra={"ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-sonnet-5"})

    def test_agente_desconhecido_em_sonnet(self):
        self.barra(chamada("tipo-que-nao-existe", "sonnet"))

    def test_sem_a_guarda_de_escrita_nenhum_agente_com_bash_roda_em_sonnet(self):
        """A lista de quem pode é a da guarda; sem a guarda, ninguém é guardado."""
        with tempfile.TemporaryDirectory(prefix="hook-sem-guarda-") as pasta:
            destino = Path(pasta) / "hooks"
            (destino / "lib").mkdir(parents=True)
            shutil.copy(HOOK, destino / HOOK.name)
            shutil.copy(HOOK.parent / "lib" / "bloqueio.sh", destino / "lib" / "bloqueio.sh")
            self.barra(chamada("investigador"), hook=destino / HOOK.name)
            self.passa(chamada("leitor-puro"), hook=destino / HOOK.name)

    def test_sem_python_barra_sonnet_fora_da_guarda(self):
        self.barra(chamada("general-purpose", "sonnet"), path=self.sem_python())
        self.barra(chamada("engenheiro-go", "claude-sonnet-5"), path=self.sem_python())


class TestePassa(Bancada):
    def test_passa_sonnet_opus_fable_e_modelo_ausente(self):
        """Os quatro casos que a especificação exige, cada um no papel que a ordem lhe dá."""
        self.passa(chamada("documentador-de-contexto", "sonnet"))
        self.passa(chamada("general-purpose", "opus"))
        self.passa(chamada("general-purpose", "fable"))
        self.passa(chamada("general-purpose"))

    def test_opus_e_fable_em_qualquer_agente(self):
        for tipo in ("general-purpose", "Explore", "Plan", "engenheiro-go", "statusline-setup", "editor-sonnet"):
            for modelo in ("opus", "fable", "claude-opus-5-5", "claude-fable-5-1", "opus[1m]"):
                with self.subTest(tipo=tipo, modelo=modelo):
                    self.passa(chamada(tipo, modelo))

    def test_sonnet_nos_agentes_de_contexto_guardados(self):
        for tipo in ("investigador", "documentador-de-contexto"):
            for modelo in (None, "sonnet", "claude-sonnet-5"):
                with self.subTest(tipo=tipo, modelo=modelo):
                    self.passa(chamada(tipo, modelo))

    def test_sonnet_em_agente_so_de_leitura(self):
        for tipo in ("leitor-puro", "leitor-lista", "leitor-negado"):
            with self.subTest(tipo=tipo):
                self.passa(chamada(tipo))
        self.passa(chamada("leitor-puro", "sonnet"))

    def test_sem_python_sonnet_no_agente_guardado(self):
        self.passa(chamada("investigador", "sonnet"), path=self.sem_python())

    def test_sem_modelo_em_lugar_nenhum(self):
        self.passa(chamada("general-purpose"))
        self.passa(chamada("sem-modelo"))
        self.passa(chamada("tipo-que-nao-existe"))

    def test_definicao_opus_e_herdeiro(self):
        self.passa(chamada("engenheiro-go"))
        self.passa(chamada("herdeiro"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"})

    def test_parametro_vence_definicao_haiku(self):
        self.passa(chamada("leitor-barato", "opus"))
        self.passa(chamada("claude-code-guide", "opus"))

    def test_agente_de_projeto_sobrepoe_o_de_usuario(self):
        self.passa(chamada("sobreposto"))

    def test_explore_e_plan_nao_seguem_a_variavel_sozinha(self):
        """Doc oficial: CLAUDE_CODE_SUBAGENT_MODEL sozinha não muda Explore nem Plan."""
        self.passa(chamada("Explore"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"})
        self.passa(chamada("Plan"), env_extra={"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"})

    def test_settings_do_projeto(self):
        """O env que o .claude/settings.json declara: variável opus e aliases fixados na versão."""
        fixado = {"CLAUDE_CODE_SUBAGENT_MODEL": "opus", "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-5-5",
                  "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-fable-5-1", "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-sonnet-5",
                  "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-sonnet-5"}
        self.passa(chamada("general-purpose"), env_extra=fixado)
        self.passa(chamada("investigador"), env_extra=fixado)
        self.passa(chamada(modelo="fable"), env_extra=fixado)

    def test_outra_ferramenta_nao_e_julgada(self):
        self.passa({"command": "echo haiku sonnet"}, ferramenta="Bash")

    def test_payload_vazio(self):
        p = self.roda(bruto="")
        self.assertEqual(p.returncode, 0)

    def test_json_invalido_nao_barra_e_avisa(self):
        p = self.roda(bruto="{isto não é json")
        self.assertEqual(p.returncode, 0)
        aviso = json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("não foi conferida", aviso)


class TesteContratoDaMensagem(Bancada):
    def test_bloqueio_de_haiku_em_json_deny_cita_a_ordem_e_a_alternativa(self):
        p = self.barra(chamada("leitor-barato"))
        especifico = json.loads(p.stdout)["hookSpecificOutput"]
        self.assertEqual(especifico["permissionDecision"], "deny")
        motivo = especifico["permissionDecisionReason"].lower()
        self.assertIn("ordem do dono, 2026-09-22", motivo)
        self.assertIn("sonnet para contexto", motivo)
        self.assertIn("opus para execução", motivo)
        self.assertIn("leitor-barato", especifico["permissionDecisionReason"])
        self.assertIn("documentador-de-contexto", especifico["additionalContext"])
        self.assertIn("2026-09-22", p.stderr)

    def test_bloqueio_de_sonnet_diz_por_que_o_agente_edita(self):
        casos = {
            "general-purpose": "embutido",
            "editor-sonnet": "Edit",
            "sonnet-sem-tools": "herda todas",
            "sonnet-com-memoria": "memory",
            "sonnet-com-mcp": "mcpServers",
            "sonnet-com-bash": "Bash",
        }
        for tipo, porque in casos.items():
            with self.subTest(tipo=tipo):
                p = self.barra(chamada(tipo, "sonnet"))
                especifico = json.loads(p.stdout)["hookSpecificOutput"]
                self.assertEqual(especifico["permissionDecision"], "deny")
                motivo = especifico["permissionDecisionReason"]
                self.assertIn("Sonnet 5 só colhe contexto", motivo)
                self.assertIn("ordem do dono, 2026-09-22", motivo.lower())
                self.assertIn("investigador ou documentador-de-contexto", motivo)
                self.assertIn("opus", motivo)
                self.assertIn(tipo, motivo)
                self.assertIn(porque, motivo)


class TesteMutacao(Bancada):
    """Se a ordem de resolução ou a regra do Sonnet for desligada, estes casos denunciam."""

    def test_os_tres_caminhos_ate_o_haiku(self):
        casos = [
            (chamada(modelo="claude-haiku-4-5-20251001"), {}),
            (chamada("leitor-barato"), {}),
            (chamada("general-purpose"), {"CLAUDE_CODE_SUBAGENT_MODEL": "haiku"}),
        ]
        for entrada, env_extra in casos:
            with self.subTest(entrada=entrada, env=env_extra):
                self.assertEqual(self.roda(entrada, env_extra=env_extra).returncode, 2)

    def test_os_tres_caminhos_ate_o_sonnet_que_edita(self):
        casos = [
            (chamada(modelo="claude-sonnet-5"), {}),
            (chamada("editor-sonnet"), {}),
            (chamada("general-purpose"), {"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"}),
        ]
        for entrada, env_extra in casos:
            with self.subTest(entrada=entrada, env=env_extra):
                self.assertEqual(self.roda(entrada, env_extra=env_extra).returncode, 2)


if __name__ == "__main__":
    if not HOOK.is_file():
        print(f"hook ausente: {HOOK}", file=sys.stderr)
        sys.exit(2)
    sintaxe = subprocess.run(["bash", "-n", str(HOOK)], capture_output=True, text=True)
    if sintaxe.returncode != 0:
        print(f"erro de sintaxe em {HOOK}:\n{sintaxe.stderr}", file=sys.stderr)
        sys.exit(2)
    unittest.main(verbosity=2)
