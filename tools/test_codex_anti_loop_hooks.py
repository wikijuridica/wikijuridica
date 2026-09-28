#!/usr/bin/env python3
"""Focused contracts for the official Codex anti-loop lifecycle adapter."""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / ".codex" / "hooks" / "anti_loop.py"
SPEC = importlib.util.spec_from_file_location("portal_codex_anti_loop", HOOK_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {HOOK_PATH}")
anti_loop = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = anti_loop
SPEC.loader.exec_module(anti_loop)


def digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def pre_payload(
    command: str = "go test ./internal/example",
    *,
    tool_name: str = "Bash",
    tool_input: dict | None = None,
    tool_use_id: str = "tool-pre",
) -> dict:
    return {
        "session_id": "session-1",
        "turn_id": "turn-1",
        "transcript_path": None,
        "cwd": str(ROOT),
        "hook_event_name": "PreToolUse",
        "model": "gpt-5.6",
        "permission_mode": "dontAsk",
        "tool_name": tool_name,
        "tool_input": tool_input if tool_input is not None else {"command": command},
        "tool_use_id": tool_use_id,
    }


def post_payload(
    command: str,
    response: object,
    *,
    tool_name: str = "Bash",
    tool_input: dict | None = None,
    tool_use_id: str = "tool-post",
) -> dict:
    value = pre_payload(command, tool_name=tool_name, tool_input=tool_input, tool_use_id=tool_use_id)
    value["hook_event_name"] = "PostToolUse"
    value["tool_response"] = response
    return value


def stop_payload(*, active: bool, turn_id: str = "turn-stop") -> dict:
    return {
        "session_id": "session-1",
        "turn_id": turn_id,
        "transcript_path": None,
        "cwd": str(ROOT),
        "hook_event_name": "Stop",
        "model": "gpt-5.6",
        "permission_mode": "dontAsk",
        "stop_hook_active": active,
        "last_assistant_message": "ignored unstable conversational text",
    }


def zero_delta(*, regressions: list[str] | None = None, positive: bool = False) -> dict:
    return {
        "before_evidence_digest": digest("before"),
        "after_evidence_digest": digest("after"),
        "blockers_reduced": 0,
        "approved_added": 0,
        "release_ready_added": 0,
        "public_indexable_added": 0,
        "eligible_unique_added": 0,
        "source_verified_added": 0,
        "quality_score_delta": 0,
        "regression_codes": regressions or [],
        "positive": positive,
        "regressed": bool(regressions),
    }


def product(
    *, evidence: str, blockers: int = 10, approved: int = 0, release_ready: int = 0,
    public_indexable: int = 0, eligible_unique: int = 0, source_verified: int = 0,
    quality_score: int = 0, oab_regressions: int = 0, ptbr_regressions: int = 0,
) -> dict:
    return {
        "evidence_digest": digest(evidence),
        "blockers": blockers,
        "approved": approved,
        "release_ready": release_ready,
        "public_indexable": public_indexable,
        "eligible_unique": eligible_unique,
        "source_verified": source_verified,
        "quality_score": quality_score,
        "regressions": {
            "official_source": 0,
            "legal_claims": 0,
            "pt_br": ptbr_regressions,
            "oab": oab_regressions,
            "deduplication": 0,
            "html": 0,
            "crawl": 0,
            "unauthorized_publication": 0,
        },
    }


def unit_state(
    *,
    stage: str,
    subject: str,
    evidence: str,
    causal_evidence: str,
    circuit: str,
    public_indexable: int = 0,
    oab_regressions: int = 0,
    final_product: dict | None = None,
    attempts: list[dict] | None = None,
    active_lease: dict | None = None,
    observation_epoch: int = 1,
) -> dict:
    return {
        "schema_version": 2,
        "work_unit_key": digest(f"work:{stage}:{subject}:{causal_evidence}"),
        "lineage_key": digest(f"lineage:{stage}:{subject}"),
        "spec": {
            "goal_epoch": "goal-2026-07-05",
            "stage": stage,
            "subject": subject,
            "family": subject,
            "shard": "",
            "url": "",
            "producer_version": anti_loop.GOAL_BASELINE_PRODUCER_VERSION,
            "implementation_digest": anti_loop._allowed_producer_digests()[anti_loop.GOAL_BASELINE_PRODUCER_VERSION],
            "causal_evidence_digest": digest(causal_evidence),
            "input_digests": [{"name": "input", "digest": digest("input")}],
            "gate_config_digest": digest("gates"),
            "official_source_revision": "official-source-2026-07-21",
            "output_contract": digest("contract"),
        },
        "circuit": {
            "status": circuit,
            "reason": "",
            "opened_at": "",
            "blocker_signature": "",
            "causal_evidence_digest": digest(causal_evidence),
        },
        "product": final_product or product(
            evidence=evidence,
            public_indexable=public_indexable,
            oab_regressions=oab_regressions,
        ),
        "observation_epoch": observation_epoch,
        "lineage_observation_epoch": observation_epoch,
        "attempt_sequence": 1 if attempts else 0,
        "attempts": attempts or [],
        "active_lease": active_lease,
        "terminal_blocker_signature": "",
        "publication_allowed": False,
        "render_allowed": False,
        "sitemap_allowed": False,
        "public_path": "",
        "index_policy": "noindex",
    }


def sealed_cli_response(
    *,
    kind: str,
    stage: str,
    subject: str,
    evidence: str,
    causal_evidence: str,
    circuit: str = "closed",
    attempt_status: str = "succeeded",
    delta: dict | None = None,
    public_indexable: int = 0,
    oab_regressions: int = 0,
    before_product: dict | None = None,
    after_product: dict | None = None,
) -> str:
    after = after_product or product(
        evidence=evidence,
        public_indexable=public_indexable,
        oab_regressions=oab_regressions,
    )
    before = before_product or after
    actual_delta = delta or anti_loop._derived_delta(before, after)
    lease = {
        "lease_id": "fixture-lease",
        "attempt_id": digest("fixture-attempt"),
        "claimed_at": "2026-07-21T12:00:00Z",
        "deadline": "2026-07-21T12:02:00Z",
    }
    attempt = {
        "sequence": 1,
        "baseline_epoch": 1,
        "baseline_lineage_epoch": 1,
        "lease": lease,
        "status": attempt_status if kind == "finish" else "running",
        "finished_at": "2026-07-21T12:01:00Z" if kind == "finish" else "",
        "blocker_signature": digest("fixture-deterministic-blocker") if attempt_status == "deterministic_failure" else "",
        "baseline": before,
        "product": after if kind == "finish" else before,
        "delta": actual_delta if kind == "finish" else anti_loop._derived_delta(before, before),
    }
    attempts = [attempt] if kind in {"claim", "finish"} else []
    observation_epoch = 2 if before != after else 1
    state = unit_state(
        stage=stage,
        subject=subject,
        evidence=evidence,
        causal_evidence=causal_evidence,
        circuit=circuit,
        public_indexable=public_indexable,
        oab_regressions=oab_regressions,
        final_product=after,
        attempts=attempts,
        active_lease=lease if kind == "claim" else None,
        observation_epoch=observation_epoch,
    )
    typed: dict | None
    if kind == "record":
        typed = {"created": True, "previous_product": before, "delta": actual_delta, "state": state}
    elif kind == "claim":
        typed = {"attempt": attempt, "state": state}
    elif kind == "finish":
        typed = {"attempt": attempt, "state": state}
    elif kind == "status":
        typed = None
    else:
        raise AssertionError(kind)

    result = {
        "kind": kind,
        "state": state,
        "state_digest": anti_loop.receipt_state_digest(state),
        "evidence_digest": state["product"]["evidence_digest"],
        "producer_digest": state["spec"]["implementation_digest"],
        "producer_version": state["spec"]["producer_version"],
    }
    if kind != "status":
        result[f"{kind}_result"] = typed
    envelope = {
        "schema_version": 1,
        "protocol": anti_loop.RECEIPT_PROTOCOL,
        "command": kind,
        "ok": True,
        "code": {"record": "recorded", "claim": "claimed", "finish": "finished", "status": "status"}[kind],
        "exit_code": 0,
        "message": "",
        "record_result": typed if kind == "record" else None,
        "claim_result": typed if kind == "claim" else None,
        "finish_result": typed if kind == "finish" else None,
        "state": state if kind == "status" else None,
        "result": result,
    }
    envelope["result_digest"] = anti_loop.receipt_digest(envelope)
    return json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def factory_post(response: str, *, kind: str) -> dict:
    command = f"{ROOT}/tools/go-modern run ./cmd/factory-workqueue {kind} --db /tmp/private/queue.pebble --input -"
    return post_payload(command, response)


def baseline_adapter_post(response: str) -> dict:
    return post_payload(f"{ROOT}/tools/generate-goal-baseline", response)


class AntiLoopHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="codex-anti-loop-test-")
        self.state_dir = Path(self.temp.name) / "state"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def process(self, payload: dict, *, now: float = 1.0) -> dict | None:
        return anti_loop.process_event(payload, state_dir=self.state_dir, now=now)

    def open_test_circuit(self, scope: str = "internal/foo", *, base: float = 1.0) -> str:
        command = f"timeout 10s go test ./{scope} -run TestContract --timeout 5s"
        failure = "Exit code: 1\nFAIL contract: blocker stable; pid=123; elapsed 2s\n"
        self.assertIsNone(self.process(post_payload(command, failure), now=base))
        notice = self.process(post_payload(command, failure), now=base + 1)
        self.assertIn("PostToolUse", notice["hookSpecificOutput"]["hookEventName"])
        return command

    def test_hooks_json_is_single_official_shape_without_git_scan(self) -> None:
        self.assertEqual(list((ROOT / ".codex").rglob("hooks.json")), [ROOT / ".codex" / "hooks.json"])
        self.assertNotIn("[hooks", (ROOT / ".codex" / "config.toml").read_text())
        config = json.loads((ROOT / ".codex" / "hooks.json").read_text())
        self.assertEqual(set(config["hooks"]), {"PreToolUse", "PostToolUse", "Stop"})
        script_digest = anti_loop.integrity_bundle_digest()
        bundle_paths = {
            path.relative_to(ROOT).as_posix() for path in anti_loop._integrity_bundle_files()
        }
        self.assertTrue({
            ".codex/hooks/anti_loop.py",
            "cmd/generate-goal-baseline/main.go",
            "internal/factorygoalbaseline/runner.go",
            "internal/factoryworkqueue/hook_receipt.go",
            "tools/generate-goal-baseline",
        }.issubset(bundle_paths))
        self.assertTrue({
            "go.mod", "go.sum", "tools/go-modern", "tools/run-generate-supervised",
            "tools/run-heavy-throttled", "tools/run-go-cmd-cached",
        }.isdisjoint(bundle_paths))
        expected_command = (
            "/usr/bin/python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/anti_loop.py\" "
            f"--expected-bundle-digest {script_digest}"
        )
        required_names = {
            "Bash", "apply_patch", "update_goal",
        }
        for event, groups in config["hooks"].items():
            self.assertEqual(len(groups), 1)
            if event == "Stop":
                self.assertNotIn("matcher", groups[0])
            else:
                matcher = re.compile(groups[0]["matcher"])
                self.assertFalse({name for name in required_names if matcher.fullmatch(name) is None})
                self.assertTrue(all(matcher.fullmatch(name) is None for name in (
                    "exec", "functions.exec", "exec_command", "Edit", "Write",
                )))
            for hook in groups[0]["hooks"]:
                self.assertEqual(hook["type"], "command")
                self.assertEqual(hook["timeout"], 1)
                self.assertEqual(hook["command"], expected_command)
                self.assertEqual(hook["command"].count("git rev-parse --show-toplevel"), 1)

    def test_transitive_digest_mismatch_keeps_bounded_repair_lane_and_stop_recursion_guard(self) -> None:
        command = [sys.executable, str(HOOK_PATH), "--expected-bundle-digest", digest("wrong-script")]

        def invoke(payload: dict) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                command, cwd=ROOT, input=json.dumps(payload), text=True,
                capture_output=True, timeout=5, check=False,
            )

        inspection = invoke(pre_payload("git status --short"))
        self.assertEqual(inspection.returncode, 0, inspection.stderr)
        self.assertEqual(inspection.stdout, "")

        repair_patch = "*** Begin Patch\n*** Update File: .codex/hooks/anti_loop.py\n@@\n-old\n+new\n*** End Patch"
        repair = invoke(pre_payload(tool_name="apply_patch", tool_input={"command": repair_patch}))
        self.assertEqual(repair.stdout, "")

        unrelated_patch = "*** Begin Patch\n*** Update File: README.md\n@@\n-old\n+new\n*** End Patch"
        unrelated = json.loads(invoke(pre_payload(
            tool_name="apply_patch", tool_input={"command": unrelated_patch}
        )).stdout)
        self.assertEqual(unrelated["hookSpecificOutput"]["permissionDecision"], "deny")

        material = json.loads(invoke(pre_payload("go test ./internal/factoryworkqueue")).stdout)
        self.assertEqual(material["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("bundle transitivo", material["hookSpecificOutput"]["permissionDecisionReason"])

        first_stop = json.loads(invoke(stop_payload(active=False)).stdout)
        self.assertEqual(first_stop, {
            "decision": "block",
            "reason": first_stop["reason"],
        })
        self.assertIn("bundle transitivo", first_stop["reason"])
        recursive_stop = invoke(stop_payload(active=True, turn_id="recursive"))
        self.assertEqual(recursive_stop.stdout, "")

    def test_official_payloads_and_outputs_are_exact(self) -> None:
        denied = self.process(pre_payload("git reset --hard HEAD"))
        self.assertEqual(set(denied), {"hookSpecificOutput"})
        self.assertEqual(
            set(denied["hookSpecificOutput"]),
            {"hookEventName", "permissionDecision", "permissionDecisionReason"},
        )
        self.assertEqual(denied["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn("continue", denied)

        invalid_factory = self.process(factory_post("not-json", kind="status"), now=2)
        self.assertEqual(set(invalid_factory), {"hookSpecificOutput"})
        self.assertEqual(
            set(invalid_factory["hookSpecificOutput"]),
            {"hookEventName", "additionalContext"},
        )
        self.assertEqual(invalid_factory["hookSpecificOutput"]["hookEventName"], "PostToolUse")

        stopped = self.process(stop_payload(active=False), now=3)
        self.assertEqual(set(stopped), {"decision", "reason"})
        self.assertEqual(stopped["decision"], "block")

    def test_semantic_identity_ignores_head_tmp_pid_workers_timeout(self) -> None:
        first = pre_payload(
            "timeout 90s env WORKERS=2 go test ./internal/foo -run TestX --timeout 10s /tmp/run-a HEAD pid=123"
        )
        second = pre_payload(
            "timeout 5m env WORKERS=99 go test ./internal/foo -run TestX --timeout 900s /var/tmp/run-b deadbeef pid=999"
        )
        self.assertEqual(anti_loop.semantic_identity(first).semantic_key, anti_loop.semantic_identity(second).semantic_key)
        changed = pre_payload("go test ./internal/bar -run TestX")
        self.assertNotEqual(anti_loop.semantic_identity(first).semantic_key, anti_loop.semantic_identity(changed).semantic_key)
        different_selector = pre_payload("go test ./internal/foo -run TestY")
        self.assertNotEqual(anti_loop.semantic_identity(first).semantic_key, anti_loop.semantic_identity(different_selector).semantic_key)

        comment_patch = pre_payload(
            tool_name="apply_patch",
            tool_input={"command": "*** Begin Patch\n*** Update File: internal/foo/x.go\n@@\n-// a\n+// b\n*** End Patch"},
        )
        code_patch = pre_payload(
            tool_name="apply_patch",
            tool_input={"command": "*** Begin Patch\n*** Update File: internal/foo/x.go\n@@\n-return 1\n+return 2\n*** End Patch"},
        )
        self.assertEqual(anti_loop.semantic_identity(comment_patch).semantic_key, anti_loop.semantic_identity(code_patch).semantic_key)

        classifications = {
            "env CI=1 timeout 30s nice -n 10 ./tools/go-modern test ./internal/foo": "test",
            "bash -lc './tools/go-modern run ./cmd/check --profile fast'": "check",
            "sh -c './tools/go-modern run ./cmd/generate-pages --input data/a.jsonl'": "produce",
            "timeout --foreground 20s ./tools/go-modern build ./cmd/factory-workqueue": "build",
            "python3 -m pytest tools/test_codex_anti_loop_hooks.py": "test",
        }
        for command, operation in classifications.items():
            identity = anti_loop.semantic_identity(
                pre_payload(tool_name="exec", tool_input={"cmd": command})
            )
            self.assertEqual(identity.operation, operation, command)

    def test_inspection_and_patch_stdout_never_create_false_circuits(self) -> None:
        inspections = [
            "git status --short",
            "git diff -- internal/foo/x.go",
            "rg -n contract internal/foo",
            "sed -n 1,80p internal/foo/x.go",
        ]
        for index in range(100):
            command = inspections[index % len(inspections)]
            self.assertIsNone(self.process(pre_payload(command), now=100 + index))
            self.assertIsNone(self.process(post_payload(command, "same read-only output"), now=100.1 + index))
        for index in range(10):
            patch = (
                "*** Begin Patch\n*** Update File: internal/foo/x.go\n@@\n"
                f"-value-{index}\n+value-{index + 1}\n*** End Patch"
            )
            payload = pre_payload(tool_name="apply_patch", tool_input={"command": patch})
            self.assertIsNone(self.process(payload, now=300 + index))
            self.assertIsNone(self.process(
                post_payload("", "Done!", tool_name="apply_patch", tool_input={"command": patch}),
                now=300.1 + index,
            ))

    def test_scope_bound_content_patch_authorizes_exactly_one_material_retest(self) -> None:
        internal = ROOT / "internal"
        with tempfile.TemporaryDirectory(prefix=".anti-loop-scope-", dir=internal) as scoped_temp, tempfile.TemporaryDirectory(
            prefix=".anti-loop-outside-", dir=internal
        ) as outside_temp:
            scoped = Path(scoped_temp)
            outside = Path(outside_temp)
            scoped_file = scoped / "contract.go"
            outside_file = outside / "unrelated.go"
            scoped_file.write_text("package contract\n\nconst Value = 1\n")
            outside_file.write_text("package unrelated\n\nconst Value = 1\n")
            scope_rel = scoped.relative_to(ROOT).as_posix()
            command = f"go test ./{scope_rel} -run TestContract"
            failure = "Exit code: 1\nFAIL stable contract"
            self.assertIsNone(self.process(post_payload(command, failure), now=10))
            opened = self.process(post_payload(command, failure), now=11)
            self.assertIn("abriu circuito", opened["hookSpecificOutput"]["additionalContext"])
            self.assertIsNotNone(self.process(pre_payload(command), now=11.1))

            outside_file.write_text("package unrelated\n\nconst Value = 2\n")
            outside_rel = outside_file.relative_to(ROOT).as_posix()
            outside_patch = (
                "*** Begin Patch\n"
                f"*** Update File: {outside_rel}\n"
                "@@\n-const Value = 1\n+const Value = 2\n"
                "*** End Patch"
            )
            self.assertIsNone(self.process(post_payload(
                "", "Done!", tool_name="apply_patch", tool_input={"command": outside_patch}
            ), now=12))
            self.assertIsNotNone(self.process(pre_payload(command), now=12.1))

            scoped_file.write_text("package contract\n\nconst Value = 2\n")
            scoped_rel = scoped_file.relative_to(ROOT).as_posix()
            scoped_patch = (
                "*** Begin Patch\n"
                f"*** Update File: {scoped_rel}\n"
                "@@\n-const Value = 1\n+const Value = 2\n"
                "*** End Patch"
            )
            authorized = self.process(post_payload(
                "", "Done!", tool_name="apply_patch", tool_input={"command": scoped_patch}
            ), now=13)
            self.assertIn("exatamente um reteste", authorized["hookSpecificOutput"]["additionalContext"])
            self.assertIsNone(self.process(pre_payload(command), now=13.1))
            self.assertIsNotNone(self.process(pre_payload(command), now=13.2))

            closed = self.process(post_payload(command, "Exit code: 0\nok"), now=14)
            context = closed["hookSpecificOutput"]["additionalContext"]
            self.assertIn("fechou o probe", context)
            self.assertIn("não declara ProductDelta", context)
            self.assertIsNone(self.process(pre_payload(command), now=14.1))

            self.process(post_payload(command, failure), now=15)
            self.process(post_payload(command, failure), now=16)
            scoped_file.write_text("package contract\n\nconst Value = 2 // comment only\n")
            comment_patch = (
                "*** Begin Patch\n"
                f"*** Update File: {scoped_rel}\n"
                "@@\n-// old\n+// new\n"
                "*** End Patch"
            )
            self.assertIsNone(self.process(post_payload(
                "", "Done!", tool_name="apply_patch", tool_input={"command": comment_patch}
            ), now=17))
            self.assertIsNotNone(self.process(pre_payload(command), now=17.1))

    def test_repo_scope_test_check_and_build_require_new_patch_bytes(self) -> None:
        internal = ROOT / "internal"
        with tempfile.TemporaryDirectory(prefix=".anti-loop-repo-scope-", dir=internal) as target_temp:
            target = Path(target_temp)
            target_file = target / "contract.go"
            target_file.write_text("package contract\n\nconst Value = 1\n")
            target_rel = target_file.relative_to(ROOT).as_posix()
            value = 1
            for index, command in enumerate(("go test", "go vet", "go build")):
                with self.subTest(command=command):
                    base = 100 + index * 20
                    failure = f"Exit code: 1\nFAIL stable {command} contract"
                    self.assertIsNone(self.process(post_payload(command, failure), now=base))
                    self.assertIsNotNone(self.process(post_payload(command, failure), now=base + 1))
                    self.assertIsNotNone(self.process(pre_payload(command), now=base + 1.1))

                    target_file.write_text(
                        f"package contract\n\nconst Value = {value}\n// comment {index}\n"
                    )
                    comment_patch = (
                        "*** Begin Patch\n"
                        f"*** Update File: {target_rel}\n"
                        "@@\n-// old comment\n+// new comment\n"
                        "*** End Patch"
                    )
                    self.assertIsNone(self.process(post_payload(
                        "", "Done!", tool_name="apply_patch", tool_input={"command": comment_patch}
                    ), now=base + 2))
                    self.assertIsNotNone(self.process(pre_payload(command), now=base + 2.1))

                    next_value = value + 1
                    target_file.write_text(
                        f"package contract\n\nconst Value = {next_value}\n// comment {index}\n"
                    )
                    patch = (
                        "*** Begin Patch\n"
                        f"*** Update File: {target_rel}\n"
                        f"@@\n-const Value = {value}\n+const Value = {next_value}\n"
                        "*** End Patch"
                    )
                    armed = self.process(post_payload(
                        "", "Done!", tool_name="apply_patch", tool_input={"command": patch}
                    ), now=base + 3)
                    self.assertIn(
                        "exatamente um reteste",
                        armed["hookSpecificOutput"]["additionalContext"],
                    )
                    self.assertIsNone(self.process(pre_payload(command), now=base + 3.1))
                    self.assertIsNotNone(self.process(pre_payload(command), now=base + 3.2))

                    reopened = self.process(post_payload(command, failure), now=base + 4)
                    self.assertIn("probe_same_failure", reopened["hookSpecificOutput"]["additionalContext"])
                    self.assertIsNone(self.process(post_payload(
                        "", "Done!", tool_name="apply_patch", tool_input={"command": patch}
                    ), now=base + 5))
                    self.assertIsNotNone(self.process(pre_payload(command), now=base + 5.1))

                    final_value = next_value + 1
                    target_file.write_text(
                        f"package contract\n\nconst Value = {final_value}\n// comment {index}\n"
                    )
                    new_patch = (
                        "*** Begin Patch\n"
                        f"*** Update File: {target_rel}\n"
                        f"@@\n-const Value = {next_value}\n+const Value = {final_value}\n"
                        "*** End Patch"
                    )
                    self.assertIsNotNone(self.process(post_payload(
                        "", "Done!", tool_name="apply_patch", tool_input={"command": new_patch}
                    ), now=base + 6))
                    self.assertIsNone(self.process(pre_payload(command), now=base + 6.1))
                    closed = self.process(post_payload(command, "Exit code: 0\nok"), now=base + 7)
                    self.assertIn("não declara ProductDelta", closed["hookSpecificOutput"]["additionalContext"])
                    self.assertIsNone(self.process(pre_payload(command), now=base + 7.1))
                    value = final_value

    def test_destructive_git_variants_are_denied_but_explicit_pathspec_is_allowed(self) -> None:
        denied = (
            "/usr/bin/git switch other",
            "command git rm internal/foo/x.go",
            "git add .",
            "git add -- .",
            "git add -u",
            "git add -- '*.go'",
            "git add -- internal",
            "git add -- /opt/wiki",
            "/usr/bin/git reset --hard HEAD",
            "git -C /opt/wiki reset --hard HEAD",
            "git read-tree HEAD",
            "git apply -R unsafe.patch",
            "git commit -am unsafe",
            "git commit -m unsafe",
            "git commit -m unsafe -- .",
            "git commit -m unsafe -- internal",
            "git commit -m unsafe --no-verify -- internal/foo/x.go",
            "git commit -m unsafe -o internal/hidden.go -- internal/foo/x.go",
            "bash -lc 'git restore --source=HEAD internal/foo/x.go'",
            "sudo -n git reset --hard HEAD",
            "eval 'git reset --hard HEAD'",
            "printf '%s\\0' ignored | xargs -0 git reset --hard HEAD",
            "find . -maxdepth 0 -exec git reset --hard HEAD ';'",
            "parallel git reset --hard HEAD ::: one",
            "python3 -c 'import os; os.system(\"git reset --hard HEAD\")'",
            "bash -c 'bash -c \"bash -c \\\"bash -c \\\\\\\"bash -c \\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"bash -c \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"git reset --hard HEAD\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\"\\\\\\\\\\\\\\\"\\\\\\\"\\\"\"'",
        )
        for tool_name in ("Bash", "exec", "functions.exec", "exec_command"):
            for command in denied:
                key = "cmd" if tool_name != "Bash" else "command"
                output = self.process(pre_payload(tool_name=tool_name, tool_input={key: command}))
                self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny", (tool_name, command))
        self.assertIsNone(self.process(pre_payload("git add -- internal/foo/x.go")))
        self.assertIsNone(self.process(pre_payload("git commit -m safe -- internal/foo/x.go")))
        self.assertIsNone(self.process(pre_payload("git apply --check safe.patch")))
        self.assertIsNone(self.process(pre_payload("git ls-files -- internal/foo/x.go")))
        self.assertIsNone(self.process(pre_payload("printf '%s' 'git reset is documentation'")))

    def test_night_churn_replay_requires_authenticated_causal_probe(self) -> None:
        command = self.open_test_circuit()
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        denied = self.process(pre_payload(command), now=3)
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")

        # A relevant-looking patch does not authenticate causality and cannot
        # reset the repeated test result.
        patch = "*** Begin Patch\n*** Update File: internal/foo/x.go\n@@\n-old\n+new\n*** End Patch"
        self.process(post_payload("", "Exit code: 0\nSuccess", tool_name="apply_patch", tool_input={"command": patch}), now=4)
        self.assertIsNotNone(self.process(pre_payload(command), now=5))

        irrelevant = sealed_cli_response(
            kind="record", stage="test", subject="internal/bar", evidence="bar",
            causal_evidence="bar-causal", circuit="half_open",
        )
        irrelevant_notice = self.process(factory_post(irrelevant, kind="record"), now=6)
        self.assertIn("irrelevante", irrelevant_notice["hookSpecificOutput"]["additionalContext"])
        self.assertIsNotNone(self.process(pre_payload(command), now=7))

        relevant = sealed_cli_response(
            kind="record", stage="test", subject=semantic_key, evidence="foo",
            causal_evidence="foo-causal", circuit="half_open",
        )
        relevant_notice = self.process(factory_post(relevant, kind="record"), now=8)
        self.assertIn("exatamente um probe", relevant_notice["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.process(pre_payload(command), now=9))
        # The probe is atomic/consumable; a concurrent second admission fails.
        self.assertIsNotNone(self.process(pre_payload(command), now=9.1))

        failure = "Exit code: 1\nFAIL contract: blocker stable; pid=999; elapsed 900s\n"
        self.process(post_payload(command, failure), now=10)
        self.assertIsNotNone(self.process(pre_payload(command), now=10 + 31 * 60))

    def test_repeated_same_receipt_and_implementation_noise_do_not_reopen(self) -> None:
        command = self.open_test_circuit(base=10)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        receipt = sealed_cli_response(
            kind="record", stage="test", subject=semantic_key, evidence="same",
            causal_evidence="same-causal", circuit="half_open",
        )
        self.process(factory_post(receipt, kind="record"), now=12)
        self.assertIsNone(self.process(pre_payload(command), now=13))
        self.process(post_payload(command, "Exit code: 1\nFAIL same"), now=14)
        self.assertIsNotNone(self.process(pre_payload(command), now=15))
        self.process(factory_post(receipt, kind="record"), now=16)
        self.assertIsNotNone(self.process(pre_payload(command), now=17))

    def test_half_open_probe_is_atomic_under_concurrent_pre_hooks(self) -> None:
        command = self.open_test_circuit(base=17)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        receipt = sealed_cli_response(
            kind="record", stage="test", subject=semantic_key, evidence="atomic",
            causal_evidence="atomic-causal", circuit="half_open",
        )
        self.process(factory_post(receipt, kind="record"), now=19)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            outputs = list(pool.map(
                lambda _: anti_loop.process_event(pre_payload(command), state_dir=self.state_dir, now=20),
                range(2),
            ))
        self.assertEqual(sum(output is None for output in outputs), 1, outputs)
        self.assertEqual(
            sum(
                isinstance(output, dict)
                and output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
                for output in outputs
            ),
            1,
            outputs,
        )

    def test_receipt_seen_before_circuit_cannot_be_replayed_after_failure(self) -> None:
        command = "go test ./internal/foo -run TestReplay"
        failure = "Exit code: 1\nFAIL replay"
        self.assertIsNone(self.process(post_payload(command, failure), now=18))
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        receipt = sealed_cli_response(
            kind="record", stage="test", subject=semantic_key, evidence="old",
            causal_evidence="old-causal", circuit="half_open",
        )
        first_notice = self.process(factory_post(receipt, kind="record"), now=19)
        self.assertIn("ainda não bloqueada", first_notice["hookSpecificOutput"]["additionalContext"])
        self.process(post_payload(command, failure), now=20)
        replay_notice = self.process(factory_post(receipt, kind="record"), now=21)
        self.assertIn("replay não concedeu", replay_notice["hookSpecificOutput"]["additionalContext"])
        self.assertIsNotNone(self.process(pre_payload(command), now=22))

    def test_quality_regression_dominates_growth(self) -> None:
        command = self.open_test_circuit(base=20)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        before = product(evidence="before-growth", blockers=5, approved=5, release_ready=4)
        after = product(
            evidence="raw-growth", blockers=4, approved=505, release_ready=404,
            public_indexable=200, eligible_unique=9_999, source_verified=9_000,
            oab_regressions=1,
        )
        receipt = sealed_cli_response(
            kind="finish", stage="test", subject=semantic_key, evidence="raw-growth",
            causal_evidence="growth-causal", circuit="closed",
            before_product=before, after_product=after,
        )
        notice = self.process(factory_post(receipt, kind="finish"), now=22)
        self.assertIn("regressão", notice["hookSpecificOutput"]["additionalContext"])
        self.assertIsNotNone(self.process(pre_payload(command), now=23))

        completion = self.process(
            pre_payload(tool_name="update_goal", tool_input={"status": "complete"}),
            now=24,
        )
        self.assertEqual(completion["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("0/10000", completion["hookSpecificOutput"]["permissionDecisionReason"])

    def test_regression_debt_is_compared_before_to_after_not_treated_as_presence(self) -> None:
        command = self.open_test_circuit(base=25)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        before = product(evidence="debt-100", blockers=100, ptbr_regressions=100)
        after = product(evidence="debt-99", blockers=99, ptbr_regressions=99)
        receipt = sealed_cli_response(
            kind="finish", stage="test", subject=semantic_key, evidence="debt-99",
            causal_evidence="debt-reduction-causal", circuit="closed",
            before_product=before, after_product=after,
        )
        notice = self.process(factory_post(receipt, kind="finish"), now=27)
        self.assertIn("OutcomeDelta", notice["hookSpecificOutput"]["additionalContext"])
        self.assertNotIn("regressão", notice["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.process(pre_payload(command), now=28))

    def test_generic_success_is_no_delta_and_real_infrastructure_delta_is_not_public_page_delta(self) -> None:
        command = self.open_test_circuit(base=30)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        generic = sealed_cli_response(
            kind="finish", stage="test", subject=semantic_key, evidence="test-pass",
            causal_evidence="test-pass-causal", circuit="closed", attempt_status="succeeded",
        )
        notice = self.process(factory_post(generic, kind="finish"), now=32)
        context = notice["hookSpecificOutput"]["additionalContext"]
        self.assertIn("sem alegar delta", context)
        self.assertIsNotNone(self.process(pre_payload(command), now=33))

        before = product(evidence="infra-before", blockers=2)
        after = product(evidence="infra-after", blockers=1, eligible_unique=500, source_verified=50)
        receipt = sealed_cli_response(
            kind="finish", stage="test", subject=semantic_key, evidence="infra-after",
            causal_evidence="infra-causal", circuit="closed", attempt_status="succeeded",
            before_product=before, after_product=after,
        )
        notice = self.process(factory_post(receipt, kind="finish"), now=33.1)
        context = notice["hookSpecificOutput"]["additionalContext"]
        self.assertIn("infraestrutura", context)
        self.assertIn("não converte", context)
        self.assertIsNone(self.process(pre_payload(command), now=33.2))
        completion = self.process(pre_payload(tool_name="update_goal", tool_input={"status": "complete"}), now=34)
        self.assertIn("0/10000", completion["hookSpecificOutput"]["permissionDecisionReason"])

    def test_forged_receipt_from_non_cli_is_never_progress(self) -> None:
        command = self.open_test_circuit(base=40)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        receipt = sealed_cli_response(
            kind="finish", stage="test", subject=semantic_key, evidence="forged",
            causal_evidence="forged-causal", circuit="closed",
        )
        forged = post_payload("printf factory-workqueue", receipt)
        self.process(forged, now=42)
        self.assertIsNotNone(self.process(pre_payload(command), now=43))
        for fake_launcher in (
            "go run ./cmd/factory-workqueue",
            "/tmp/go-modern run ./cmd/factory-workqueue",
            "factory-workqueue",
        ):
            fake = post_payload(
                f"{fake_launcher} finish --db /tmp/private/queue.pebble --input -",
                receipt,
            )
            self.process(fake, now=43.1)
            self.assertIsNotNone(self.process(pre_payload(command), now=43.2), fake_launcher)

    def test_real_adapter_receipt_is_dispatched_and_forged_or_missing_receipt_fails_closed(self) -> None:
        adapter_command = f"{ROOT}/tools/generate-goal-baseline"
        identity = anti_loop.semantic_identity(pre_payload(adapter_command))
        terminal = sealed_cli_response(
            kind="finish",
            stage="generate-goal-baseline-preflight",
            subject="data/ops/goal_baseline.jsonl",
            evidence="adapter-deterministic",
            causal_evidence="adapter-causal",
            circuit="open",
            attempt_status="deterministic_failure",
        )
        notice = self.process(baseline_adapter_post(terminal), now=44)
        self.assertIn("falha determinística", notice["hookSpecificOutput"]["additionalContext"])
        denied = self.process(pre_payload(adapter_command), now=44.1)
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        with sqlite3.connect(self.state_dir / "anti-loop.sqlite3") as connection:
            row = connection.execute(
                "SELECT circuit,reason FROM operations WHERE semantic_key=?", (identity.semantic_key,)
            ).fetchone()
        self.assertEqual(row, ("open", "deterministic_failure"))

        repaired_causal = digest("adapter-causal-after-repair")
        probe_command = (
            f"env WIKI_FACTORY_CAUSAL_EVIDENCE_DIGEST={repaired_causal} "
            f"{ROOT}/tools/generate-goal-baseline"
        )
        self.assertIsNone(self.process(pre_payload(probe_command), now=44.2))
        repeated_probe = self.process(pre_payload(probe_command), now=44.3)
        self.assertEqual(repeated_probe["hookSpecificOutput"]["permissionDecision"], "deny")

        forged_state = Path(self.temp.name) / "forged-state"
        forged = anti_loop.process_event(
            post_payload("printf receipt", terminal), state_dir=forged_state, now=45
        )
        self.assertIsNone(forged)
        self.assertIsNone(anti_loop.process_event(
            pre_payload(adapter_command), state_dir=forged_state, now=45.1
        ))

        missing_state = Path(self.temp.name) / "missing-state"
        missing = anti_loop.process_event(
            baseline_adapter_post("producer failed without envelope"), state_dir=missing_state, now=46
        )
        self.assertIn("producer_receipt_missing", missing["hookSpecificOutput"]["additionalContext"])
        missing_denied = anti_loop.process_event(
            pre_payload(adapter_command), state_dir=missing_state, now=46.1
        )
        self.assertEqual(missing_denied["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_causal_fingerprint_collision_is_typed_on_first_result_and_routes_stop_forward(self) -> None:
        command = "./tools/bootstrap-chain"
        response = (
            "bootstrap-chain: membership/stat changed after step 17; "
            "causal fingerprint mismatch from concurrent mutation"
        )
        notice = self.process(post_payload(command, response), now=47)
        self.assertIn("causal_fingerprint_collision", notice["hookSpecificOutput"]["additionalContext"])
        denied = self.process(pre_payload(command), now=47.1)
        self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
        stopped = self.process(stop_payload(active=False, turn_id="collision-stop"), now=47.2)
        self.assertIn("causal_fingerprint_collision", stopped["reason"])
        self.assertIn("elo causal", stopped["reason"])

    def test_outer_digest_cannot_hide_final_state_or_producer_tampering(self) -> None:
        command = self.open_test_circuit(base=44)
        semantic_key = anti_loop.semantic_identity(pre_payload(command)).semantic_key
        for field in ("producer_digest", "state_digest", "evidence_digest"):
            envelope = json.loads(sealed_cli_response(
                kind="finish", stage="test", subject=semantic_key, evidence=f"tamper-{field}",
                causal_evidence=f"tamper-{field}-causal", circuit="closed",
            ))
            envelope["result"][field] = digest(f"forged-{field}")
            envelope["result_digest"] = anti_loop.receipt_digest({
                key: value for key, value in envelope.items() if key != "result_digest"
            })
            notice = self.process(factory_post(
                json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                kind="finish",
            ), now=46)
            self.assertIn("não era um receipt", notice["hookSpecificOutput"]["additionalContext"], field)
            self.assertIsNotNone(self.process(pre_payload(command), now=46.1), field)

    def test_stop_blocks_once_and_never_when_recursion_flag_is_true(self) -> None:
        first = self.process(stop_payload(active=False), now=50)
        self.assertEqual(first["decision"], "block")
        self.assertIsNone(self.process(stop_payload(active=False), now=51))
        self.assertIsNone(self.process(stop_payload(active=True, turn_id="new-turn"), now=52))

    def test_update_goal_complete_below_10k_is_denied(self) -> None:
        output = self.process(pre_payload(tool_name="update_goal", tool_input={"status": "complete"}), now=60)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("0/10000", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_private_permissions_symlink_and_corruption_recovery(self) -> None:
        self.process(post_payload("go test ./internal/private", "Exit code: 1\nFAIL"), now=70)
        database = self.state_dir / "anti-loop.sqlite3"
        self.assertEqual(self.state_dir.stat().st_mode & 0o777, 0o700)
        self.assertEqual(database.stat().st_mode & 0o777, 0o600)

        database.write_bytes(b"not a sqlite database")
        os.chmod(database, 0o600)
        recovered_command = "go test ./internal/recovered"
        self.process(post_payload(recovered_command, "Exit code: 1\nFAIL"), now=71)
        self.assertTrue((self.state_dir / "anti-loop.sqlite3.corrupt").is_file())
        with sqlite3.connect(database) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        quarantine = self.process(pre_payload(recovered_command), now=71.1)
        self.assertEqual(quarantine["hookSpecificOutput"]["permissionDecision"], "deny")
        semantic_key = anti_loop.semantic_identity(pre_payload(recovered_command)).semantic_key
        recovery_receipt = sealed_cli_response(
            kind="record", stage="test", subject=semantic_key, evidence="recovered",
            causal_evidence="recovered-causal", circuit="half_open",
        )
        self.process(factory_post(recovery_receipt, kind="record"), now=71.2)
        self.assertIsNone(self.process(pre_payload(recovered_command), now=71.3))

        with tempfile.TemporaryDirectory(prefix="anti-loop-symlink-") as temporary:
            target = Path(temporary) / "target"
            target.mkdir(mode=0o700)
            link = Path(temporary) / "linked-state"
            link.symlink_to(target, target_is_directory=True)
            output = anti_loop.process_event(post_payload("go test ./x", "FAIL"), state_dir=link)
            self.assertIsNone(output)
            self.assertFalse((target / "anti-loop.sqlite3").exists())

            real_state = Path(temporary) / "real-state"
            real_state.mkdir(mode=0o700)
            victim = Path(temporary) / "victim"
            victim.write_text("preserve")
            (real_state / "anti-loop.sqlite3").symlink_to(victim)
            anti_loop.process_event(post_payload("go test ./y", "FAIL"), state_dir=real_state)
            self.assertEqual(victim.read_text(), "preserve")

        forbidden_repo_state = ROOT / ".codex" / "hooks" / "runtime-state-must-not-exist"
        self.assertFalse(forbidden_repo_state.exists())
        anti_loop.process_event(post_payload("go test ./z", "FAIL"), state_dir=forbidden_repo_state)
        self.assertFalse(forbidden_repo_state.exists())

    def test_sqlite_sidecars_are_pinned_by_descriptor_before_mode_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="anti-loop-sidecars-") as temporary:
            state = Path(temporary) / "state"
            state.mkdir(mode=0o700)
            database = state / "anti-loop.sqlite3"
            database.write_bytes(b"")
            os.chmod(database, 0o600)

            wal = Path(str(database) + "-wal")
            wal.write_bytes(b"wal")
            os.chmod(wal, 0o644)
            anti_loop._check_sqlite_sidecars(database)
            self.assertEqual(wal.stat().st_mode & 0o777, 0o600)

            wal.unlink()
            victim = Path(temporary) / "victim"
            victim.write_text("preserve")
            wal.symlink_to(victim)
            with self.assertRaises(anti_loop.UnsafeState):
                anti_loop._check_sqlite_sidecars(database)
            self.assertEqual(victim.read_text(), "preserve")

            wal.unlink()
            shared = Path(temporary) / "shared"
            shared.write_text("shared")
            os.link(shared, Path(str(database) + "-shm"))
            with self.assertRaises(anti_loop.UnsafeState):
                anti_loop._check_sqlite_sidecars(database)

    def test_concurrent_sqlite_calls_are_bounded_and_integral(self) -> None:
        def invoke(index: int) -> None:
            anti_loop.process_event(
                post_payload(f"go test ./internal/concurrent/{index % 17}", f"Exit code: 1\nFAIL {index % 3}"),
                state_dir=self.state_dir,
                now=80 + index / 1000,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            list(pool.map(invoke, range(240)))
        database = self.state_dir / "anti-loop.sqlite3"
        with sqlite3.connect(database) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertLessEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], anti_loop.EVENT_RING_LIMIT)

    def test_more_than_512_open_circuits_are_never_evicted(self) -> None:
        deadline = time.monotonic() + 30
        with anti_loop.StateStore(self.state_dir, deadline=deadline) as store:
            identities = []
            for index in range(anti_loop.OPERATION_RING_LIMIT + 1):
                identity = anti_loop.semantic_identity(pre_payload(f"go test ./internal/open/{index}"))
                identities.append(identity)
                store.record_result(identity, digest(f"failure:{index}"), 100 + index)
                store.record_result(identity, digest(f"failure:{index}"), 100.1 + index)
            count = store.db.execute("SELECT COUNT(*) FROM operations WHERE circuit='open'").fetchone()[0]
            self.assertEqual(count, anti_loop.OPERATION_RING_LIMIT + 1)
        first = pre_payload("go test ./internal/open/0")
        self.assertEqual(self.process(first, now=1000)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_1000_core_invocations_p95_under_50ms(self) -> None:
        durations = []
        payload = post_payload("go test ./internal/perf", "Exit code: 1\nFAIL stable")
        for index in range(1000):
            started = time.perf_counter()
            anti_loop.process_event(payload, state_dir=self.state_dir, now=2000 + index / 1000)
            durations.append((time.perf_counter() - started) * 1000)
        p95 = statistics.quantiles(durations, n=100, method="inclusive")[94]
        self.assertLess(p95, 50.0, f"p95={p95:.3f}ms max={max(durations):.3f}ms")

    def test_doctor_requires_official_trust_matchers_and_real_hook_pairs(self) -> None:
        config = json.loads((ROOT / ".codex" / "hooks.json").read_text())
        event_names = {"PreToolUse": "preToolUse", "PostToolUse": "postToolUse", "Stop": "stop"}

        def hooks_list_response(trust: str) -> dict:
            hooks = []
            for configured_event, groups in config["hooks"].items():
                for group in groups:
                    for index, hook in enumerate(group["hooks"]):
                        hooks.append({
                            "key": f"fixture:{configured_event}:{index}",
                            "eventName": event_names[configured_event],
                            "handlerType": hook["type"],
                            "matcher": group.get("matcher"),
                            "command": hook["command"],
                            "timeoutSec": hook["timeout"],
                            "statusMessage": hook["statusMessage"],
                            "sourcePath": str(ROOT / ".codex" / "hooks.json"),
                            "source": "project",
                            "pluginId": None,
                            "displayOrder": index,
                            "enabled": True,
                            "isManaged": False,
                            "currentHash": digest(f"hook-{configured_event}-{index}"),
                            "trustStatus": trust,
                        })
            return {
                "id": 2,
                "result": {"data": [{
                    "cwd": str(ROOT), "hooks": hooks, "warnings": [], "errors": [],
                }]},
            }

        with tempfile.TemporaryDirectory(prefix="codex-hook-doctor-") as temporary:
            temporary_path = Path(temporary)
            fake_codex = temporary_path / "codex"
            rollout = temporary_path / "rollout.jsonl"
            fresh_timestamp = time.time() + 1
            rollout_records = [
                {"type": "response_item", "payload": {
                    "type": "custom_tool_call", "name": "exec", "call_id": "doctor-call",
                    "internal_chat_message_metadata_passthrough": {"turn_id": "doctor-turn"},
                }},
                {"type": "event_msg", "payload": {"type": "hook_started", "turn_id": "doctor-turn", "run": {
                    "id": "pre-run", "event_name": "preToolUse", "source_path": str(ROOT / ".codex" / "hooks.json"),
                    "status": "running", "handler_type": "command", "source": "project",
                }}},
                {"type": "event_msg", "payload": {"type": "hook_completed", "turn_id": "doctor-turn", "run": {
                    "id": "pre-run", "event_name": "preToolUse", "source_path": str(ROOT / ".codex" / "hooks.json"),
                    "status": "completed", "handler_type": "command", "source": "project",
                }}},
                {"method": "hook/started", "params": {"run": {
                    "id": "post-run", "eventName": "postToolUse", "sourcePath": str(ROOT / ".codex" / "hooks.json"),
                    "status": "running", "handlerType": "command", "source": "project",
                }, "turnId": "doctor-turn"}},
                {"method": "hook/completed", "params": {"run": {
                    "id": "post-run", "eventName": "postToolUse", "sourcePath": str(ROOT / ".codex" / "hooks.json"),
                    "status": "completed", "handlerType": "command", "source": "project",
                }, "turnId": "doctor-turn"}},
            ]
            for index, record in enumerate(rollout_records):
                record["timestamp"] = fresh_timestamp + index / 1000
            rollout.write_text("".join(json.dumps(record) + "\n" for record in rollout_records))

            def write_fake_server(trust: str) -> None:
                listing_literal = json.dumps(json.dumps(hooks_list_response(trust), separators=(",", ":")))
                fake_codex.write_text(
                    "#!/usr/bin/env python3\n"
                    "import json, sys\n"
                    f"listing = json.loads({listing_literal})\n"
                    "for line in sys.stdin:\n"
                    "    message = json.loads(line)\n"
                    "    if message.get('id') == 0:\n"
                    "        print(json.dumps({'id': 0, 'result': {'serverInfo': {'name': 'codex', 'version': 'fixture'}}}), flush=True)\n"
                    "    elif message.get('id') == 2:\n"
                    "        print(json.dumps(listing), flush=True)\n"
                )
                os.chmod(fake_codex, 0o755)

            command = [
                str(ROOT / "tools" / "benchmark-codex-anti-loop-hook"), "--doctor",
                "--codex-bin", str(fake_codex), "--rollout", str(rollout),
                "--doctor-timeout-seconds", "2", "--max-rollout-bytes", str(1 << 20),
            ]
            write_fake_server("trusted")
            healthy = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=8, check=False)
            self.assertEqual(healthy.returncode, 0, healthy.stderr + healthy.stdout)
            healthy_result = json.loads(healthy.stdout)
            self.assertTrue(healthy_result["passed"])
            self.assertEqual(healthy_result["rollout"]["paired_events"], ["postToolUse", "preToolUse"])
            self.assertEqual(healthy_result["rollout"]["coherent_tool_use_ids"], ["doctor-call"])

            false_pair_records = [
                rollout_records[0], rollout_records[1], rollout_records[2],
                {"type": "response_item", "payload": {
                    "type": "custom_tool_call", "name": "exec", "call_id": "different-call",
                    "internal_chat_message_metadata_passthrough": {"turn_id": "doctor-turn"},
                }},
                rollout_records[3], rollout_records[4],
            ]
            for index, record in enumerate(false_pair_records):
                record["timestamp"] = fresh_timestamp + index / 1000
            rollout.write_text("".join(json.dumps(record) + "\n" for record in false_pair_records))
            false_pair = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=8, check=False)
            self.assertEqual(false_pair.returncode, 1, false_pair.stderr + false_pair.stdout)
            self.assertIn("rollout_coherent_pre_post_chain_missing", json.loads(false_pair.stdout)["errors"])

            for record in rollout_records:
                record["timestamp"] = 1
            rollout.write_text("".join(json.dumps(record) + "\n" for record in rollout_records))
            stale = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=8, check=False)
            self.assertEqual(stale.returncode, 1, stale.stderr + stale.stdout)
            stale_errors = json.loads(stale.stdout)["errors"]
            self.assertIn("rollout_fresh_real_exec_call_missing", stale_errors)

            for index, record in enumerate(rollout_records):
                record["timestamp"] = fresh_timestamp + index / 1000
            rollout.write_text("".join(json.dumps(record) + "\n" for record in rollout_records))
            write_fake_server("untrusted")
            unhealthy = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=8, check=False)
            self.assertEqual(unhealthy.returncode, 1, unhealthy.stderr + unhealthy.stdout)
            errors = json.loads(unhealthy.stdout)["errors"]
            self.assertTrue(any(error.startswith("handler_untrusted:") for error in errors), errors)

    def test_real_factory_cli_receipt_cross_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="factory-workqueue-cross-") as temporary:
            temporary_path = Path(temporary)
            request = {
                "spec": {
                    "goal_epoch": "goal-2026-07-05",
                    "stage": "test",
                    "subject": "internal/cross-contract",
                    "family": "internal/cross-contract",
                    "shard": "",
                    "url": "",
                    "producer_version": anti_loop.GOAL_BASELINE_PRODUCER_VERSION,
                    "implementation_digest": anti_loop._allowed_producer_digests()[anti_loop.GOAL_BASELINE_PRODUCER_VERSION],
                    "causal_evidence_digest": digest("cross-causal"),
                    "input_digests": [{"name": "input", "digest": digest("cross-input")}],
                    "gate_config_digest": digest("cross-gates"),
                    "official_source_revision": "official-source-2026-07-21",
                    "output_contract": digest("cross-contract"),
                },
                "product": product(evidence="cross-product"),
                "observed_at": "2026-07-21T12:00:00Z",
            }
            command = [
                str(ROOT / "tools" / "go-modern"), "run", "./cmd/factory-workqueue", "record",
                "--db", str(temporary_path / "queue.pebble"), "--input", "-",
            ]
            completed = subprocess.run(
                command,
                cwd=ROOT,
                input=json.dumps(request),
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            tool_command = " ".join(command)
            output = self.process(post_payload(tool_command, completed.stdout), now=3000)
            self.assertIsNotNone(output)
            context = output["hookSpecificOutput"]["additionalContext"]
            self.assertIn("Factory receipt válido", context)
            self.assertNotIn("não era", context)

    def test_go_python_receipt_digest_known_vector(self) -> None:
        preimage = {
            "schema_version": 1,
            "protocol": anti_loop.RECEIPT_PROTOCOL,
            "command": "status",
            "ok": False,
            "code": "not_found",
            "exit_code": 5,
            "message": "missing",
            "result": None,
            "record_result": None,
            "claim_result": None,
            "finish_result": None,
            "state": None,
        }
        self.assertEqual(
            anti_loop.receipt_digest(preimage),
            "sha256:bcf81045b8bc36f6be99fbba304084553ac2a338830604248a7fc71e42962f4f",
        )


if __name__ == "__main__":
    unittest.main()
