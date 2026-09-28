#!/usr/bin/python3 -I
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(root: pathlib.Path, args: list[str], *, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(args, cwd=root, env=merged, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=check)


class ReferenceTransactionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="v2-ref-hook-test-")
        self.root = pathlib.Path(self.temp.name)
        run(self.root, ["git", "init", "-q"])
        run(self.root, ["git", "config", "user.name", "Fixture"])
        run(self.root, ["git", "config", "user.email", "fixture@example.invalid"])
        (self.root / ".githooks").mkdir()
        (self.root / "tools").mkdir()
        for relative in [".githooks/reference-transaction",
                         "tools/check-v2-finalized-commit"]:
            source = SOURCE_ROOT / relative
            target = self.root / relative
            target.write_bytes(source.read_bytes())
            target.chmod(0o755)
        launcher = self.root / "tools/run-v2-index-product-gates"
        launcher.write_text(
            """#!/bin/sh
set -eu
root=
old=
candidate=
while [ \"$#\" -gt 0 ]; do
    case \"$1\" in
        --root) root=\"$2\"; shift 2 ;;
        --old) old=\"$2\"; shift 2 ;;
        --candidate) candidate=\"$2\"; shift 2 ;;
        *) exit 2 ;;
    esac
done
[ -n \"$root\" ] && [ -n \"$old\" ] && [ -n \"$candidate\" ] || exit 2
printf '%s\\n' \"$old $candidate\" >>\"$root/product-launcher-invocations\"
if ! /usr/bin/git -C \"$root\" diff --quiet \"$old\" \"$candidate\" -- \\
        data/editorial/v2_writing_semantic_contract.json; then
    echo \"fixture semantic gate invoked\" >&2
    exit 43
fi
tmp=$(/usr/bin/mktemp /tmp/v2-fixture-checker.XXXXXX)
trap '/usr/bin/rm -f -- \"$tmp\"' EXIT HUP INT TERM
/usr/bin/git -C \"$root\" show \\
    \"$old:tools/check-v2-finalized-commit\" >\"$tmp\"
/usr/bin/python3.11 -I \"$tmp\" --root \"$root\" --old \"$old\" \\
    --new \"$candidate\" --product-only
""",
            encoding="utf-8",
        )
        launcher.chmod(0o755)
        (self.root / "README").write_text("fixture\n")
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        page = self.root / "data/editorial/v2_pages/base-01.jsonl"
        portfolio.parent.mkdir(parents=True)
        page.parent.mkdir(parents=True)
        portfolio.write_bytes(self.record("baseline"))
        page.write_bytes(self.record("baseline"))
        run(self.root, ["git", "add", "README", ".githooks", "tools", "data"])
        run(self.root, ["git", "commit", "-q", "-m", "base"])
        run(self.root, ["git", "config", "core.hooksPath", ".githooks"])
        self.base = run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        self.branch_ref = run(
            self.root, ["git", "symbolic-ref", "HEAD"]).stdout.strip()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def record(self, intent: str) -> bytes:
        return (json.dumps({
            "intent_id": intent,
            "public": False,
            "publication_allowed": False,
            "publication_candidate": False,
            "render_allowed": False,
            "sitemap_allowed": False,
            "indexable": False,
            "approval": False,
            "index_policy": "noindex",
            "public_path": "",
        },
                           separators=(",", ":")) + "\n").encode()

    def launcher_invocations(self) -> list[str]:
        path = self.root / "product-launcher-invocations"
        if not path.exists():
            return []
        return path.read_text(encoding="utf-8").splitlines()

    def prepare(self, portfolio: list[str], page: list[str], mode: int = 0o644) -> pathlib.Path:
        portfolio_dir = self.root / "data/editorial/portfolio_v2"
        pages_dir = self.root / "data/editorial/v2_pages"
        portfolio_dir.mkdir(parents=True, exist_ok=True)
        (portfolio_dir / "area.jsonl").write_bytes(
            b"".join(self.record(intent) for intent in portfolio))
        run(self.root, ["git", "add", "data/editorial/portfolio_v2"])
        run(self.root, ["git", "commit", "-q", "-m", "portfolio prerequisite"])
        self.base = run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        (self.root / "product-launcher-invocations").unlink(missing_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)
        target = pages_dir / "area-01.jsonl"
        target.write_bytes(b"".join(self.record(intent) for intent in page))
        target.chmod(mode)
        run(self.root, ["git", "add", "data/editorial/v2_pages"])
        return target

    def test_same_candidate_cannot_manufacture_membership(self) -> None:
        portfolio_dir = self.root / "data/editorial/portfolio_v2"
        pages_dir = self.root / "data/editorial/v2_pages"
        portfolio_dir.mkdir(parents=True, exist_ok=True)
        pages_dir.mkdir(parents=True, exist_ok=True)
        (portfolio_dir / "area.jsonl").write_bytes(self.record("existing"))
        run(self.root, ["git", "add", "data/editorial/portfolio_v2"])
        run(self.root, ["git", "commit", "-q", "-m", "existing portfolio prerequisite"])
        self.base = run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        (portfolio_dir / "area.jsonl").write_bytes(
            self.record("existing") + self.record("manufactured"))
        (pages_dir / "area-01.jsonl").write_bytes(self.record("manufactured"))
        run(self.root, ["git", "add", "data"])
        tree = run(self.root, ["git", "write-tree"]).stdout.strip()
        workflow_env = {
            "GIT_AUTHOR_NAME": "Portal Jurídico Workflow",
            "GIT_AUTHOR_EMAIL": "workflow-integrator@portal-juridico.invalid",
            "GIT_COMMITTER_NAME": "Portal Jurídico Workflow",
            "GIT_COMMITTER_EMAIL": "workflow-integrator@portal-juridico.invalid",
        }
        candidate = run(
            self.root, ["git", "commit-tree", tree, "-p", self.base],
            env=workflow_env,
        ).stdout.strip()
        entry = run(self.root, ["git", "ls-tree", candidate, "--", "data/editorial/v2_pages/area-01.jsonl"]).stdout
        mode, _kind, oid_and_path = entry.split(" ", 2)
        object_id = oid_and_path.split("\t", 1)[0]
        digest = hashlib.sha256()
        digest.update(b"v2-finalized-reference-receipt-v1\0")
        digest.update(self.base.encode() + b"\0" + candidate.encode() + b"\0")
        digest.update(
            b"data/editorial/v2_pages/area-01.jsonl\0" + mode.encode() +
            b"\0" + object_id.encode() + b"\n")
        completed = run(
            self.root,
            ["git", "update-ref", self.branch_ref, candidate, self.base],
            env={
                "WIKI_V2_AUTHENTICATED_COMMIT_OID": candidate,
                "WIKI_V2_AUTHENTICATED_OLD_OID": self.base,
                "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "mass",
                "WIKI_V2_AUTHENTICATED_CLOSURE_SHA256": digest.hexdigest(),
            },
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        # A mensagem do gate é ASCII e acionável desde 611d63d1 (2026-08-20):
        # tools/check-v2-finalized-commit, membership_hint. Asserta-se o
        # prefixo, o alvo (path:intent) e a metade que diz como corrigir —
        # encurtar a mensagem de volta reprova aqui. A régua acentuada
        # (ambiguo com acento) nunca mais casou depois daquele commit.
        self.assertIn(
            "intent fora/ambiguo no portfolio candidato: "
            "data/editorial/v2_pages/area-01.jsonl:manufactured",
            completed.stderr)
        self.assertIn("COMO CORRIGIR", completed.stderr)
        self.assertIn("check-v2-portfolio-pairing", completed.stderr)
        self.assertEqual(run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(), self.base)

    def assert_rejected(
        self, portfolio: list[str], page: list[str], mode: int = 0o644,
    ) -> None:
        self.prepare(portfolio, page, mode)
        completed = run(self.root, ["git", "commit", "--no-verify", "-m", "bad"],
                        check=False)
        self.assertNotEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(), self.base)

    def test_no_verify_orphan_is_rejected(self) -> None:
        self.assert_rejected(["portfolio-a"], ["orphan"])
        self.assertEqual(len(self.launcher_invocations()), 1)

    def test_no_verify_mixed_is_rejected(self) -> None:
        self.assert_rejected(["inside"], ["inside", "outside"])

    def test_no_verify_noncanonical_git_mode_is_rejected(self) -> None:
        self.assert_rejected(["inside"], ["inside"], 0o755)

    def test_no_verify_noncanonical_portfolio_mode_is_rejected(self) -> None:
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        portfolio.chmod(0o755)
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "bad portfolio mode"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("inventário portfolio_v2", completed.stderr)

    def test_no_verify_portfolio_only_orphan_is_rejected(self) -> None:
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        portfolio.write_bytes(self.record("replacement-without-baseline"))
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        completed = run(
            self.root, ["git", "commit", "--no-verify", "-m", "orphan stock"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn(
            "intent fora/ambiguo no portfolio candidato: "
            "data/editorial/v2_pages/base-01.jsonl:baseline",
            completed.stderr)
        self.assertIn("COMO CORRIGIR", completed.stderr)
        self.assertIn("check-v2-portfolio-pairing", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base,
        )

    def install_legacy_orphan_parent(self) -> pathlib.Path:
        """Create one historical defect without teaching the hook to accept it."""
        orphan = self.root / "data/editorial/v2_pages/legacy-01.jsonl"
        orphan.write_bytes(self.record("legacy-orphan"))
        run(self.root, ["git", "add", str(orphan.relative_to(self.root))])
        run(
            self.root,
            ["git", "-c", "core.hooksPath=/dev/null", "commit", "-q",
             "-m", "fixture legacy orphan"],
        )
        self.base = run(
            self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        (self.root / "product-launcher-invocations").unlink(missing_ok=True)
        return orphan

    def test_unchanged_legacy_orphan_does_not_deadlock_forward_commit(self) -> None:
        self.install_legacy_orphan_parent()
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        portfolio.write_bytes(
            self.record("baseline") + self.record("unrelated-backlog"))
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "safe forward delta"],
            check=False,
        )
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(len(self.launcher_invocations()), 1)

    def test_touched_legacy_orphan_must_be_fixed_in_same_commit(self) -> None:
        orphan = self.install_legacy_orphan_parent()
        record = json.loads(self.record("legacy-orphan"))
        record["title"] = "still orphaned"
        orphan.write_text(
            json.dumps(record, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        run(self.root, ["git", "add", str(orphan.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "unfixed legacy path"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("shard tocado manteve defeito legado", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base,
        )

    def test_duplicate_json_legacy_page_can_be_repaired_forward(self) -> None:
        page = self.root / "data/editorial/v2_pages/base-01.jsonl"
        duplicate = self.record("baseline").rstrip(b"\n")
        page.write_bytes(duplicate[:-1] + b',"public":false}\n')
        run(self.root, ["git", "add", str(page.relative_to(self.root))])
        run(
            self.root,
            ["git", "-c", "core.hooksPath=/dev/null", "commit", "-q",
             "-m", "fixture duplicate JSON"],
        )
        self.base = run(
            self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        (self.root / "product-launcher-invocations").unlink(missing_ok=True)
        page.write_bytes(self.record("baseline"))
        run(self.root, ["git", "add", str(page.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "normalize duplicate"],
            check=False,
        )
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)

    def test_no_verify_duplicate_unused_portfolio_intent_is_rejected(self) -> None:
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        portfolio.write_bytes(
            self.record("baseline") + self.record("unused") +
            self.record("unused"))
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "duplicate portfolio"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("intent_id duplicado no portfolio", completed.stderr)

    def test_no_verify_duplicate_active_intent_across_shards_is_rejected(self) -> None:
        duplicate = self.root / "data/editorial/v2_pages/other-01.jsonl"
        duplicate.write_bytes(self.record("baseline"))
        run(self.root, ["git", "add", str(duplicate.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "duplicate active page"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("intent ativo duplicado entre shards", completed.stderr)

    def test_internal_row_with_absent_public_booleans_remains_closed(self) -> None:
        target = self.prepare(["inside"], ["inside"])
        target.write_bytes(b'{"intent_id":"inside"}\n')
        run(self.root, ["git", "add", str(target.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "closed legacy row"],
            check=False,
        )
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)

    def test_closed_supersession_tombstone_needs_no_portfolio_membership(self) -> None:
        tombstone = self.root / "data/editorial/v2_pages/tombstone-01.jsonl"
        tombstone.write_bytes(
            b'{"intent_id":"orphan-tombstone","skipped":true,'
            b'"skip_reason":"duplicate_intent_consolidated",'
            b'"index_policy":"noindex"}\n')
        run(self.root, ["git", "add", str(tombstone.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "closed tombstone"],
            check=False,
        )
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)

    def test_no_verify_semantic_only_delta_invokes_product_launcher(self) -> None:
        contract = self.root / "data/editorial/v2_writing_semantic_contract.json"
        contract.write_text("{}\n", encoding="utf-8")
        run(self.root, ["git", "add", str(contract.relative_to(self.root))])
        completed = run(
            self.root, ["git", "commit", "--no-verify", "-m", "semantic"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("fixture semantic gate invoked", completed.stderr)

    def test_parent_launcher_must_remain_executable_git_blob(self) -> None:
        launcher = self.root / "tools/run-v2-index-product-gates"
        launcher.chmod(0o644)
        run(self.root, ["git", "add", "tools/run-v2-index-product-gates"])
        run(self.root, ["git", "commit", "--no-verify", "-m", "bad mode"])
        bad_parent = run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        portfolio = self.root / "data/editorial/portfolio_v2/extra.jsonl"
        portfolio.write_bytes(self.record("extra"))
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        completed = run(
            self.root, ["git", "commit", "--no-verify", "-m", "v2 delta"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("launcher parent não é blob executável", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            bad_parent,
        )

    def test_normal_valid_commit_needs_no_legacy_receipt(self) -> None:
        self.prepare(["inside"], ["inside"])
        completed = run(
            self.root, ["git", "commit", "-m", "normal valid"], check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(len(self.launcher_invocations()), 1)
        self.assertNotEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(), self.base)

    def test_no_verify_valid_commit_invokes_product_launcher_once(self) -> None:
        self.prepare(["inside"], ["inside"])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "valid no verify"],
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(len(self.launcher_invocations()), 1)

    def test_unrelated_commit_invokes_no_product_launcher(self) -> None:
        (self.root / "docs").mkdir()
        note = self.root / "docs/note.md"
        note.write_text("nota\n", encoding="utf-8")
        run(self.root, ["git", "add", str(note.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "docs"],
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(self.launcher_invocations(), [])

    def test_unreachable_root_commit_cannot_introduce_v2_graph(self) -> None:
        tree = run(
            self.root, ["git", "rev-parse", f"{self.base}^{{tree}}"]
        ).stdout.strip()
        candidate = run(
            self.root, ["git", "commit-tree", tree], check=True
        ).stdout.strip()
        completed = run(
            self.root,
            ["git", "update-ref", "refs/heads/unreachable-root", candidate,
             "0" * 40],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("commit raiz não pode criar grafo v2", completed.stderr)

    def test_hidden_intermediate_v2_delta_cannot_hide_behind_clean_tip(self) -> None:
        page = self.root / "data/editorial/v2_pages/base-01.jsonl"
        page.write_bytes(self.record("orphan-intermediate"))
        run(self.root, ["git", "add", str(page.relative_to(self.root))])
        bad_tree = run(self.root, ["git", "write-tree"]).stdout.strip()
        hidden = run(
            self.root,
            ["git", "commit-tree", bad_tree, "-p", self.base],
        ).stdout.strip()
        clean_tree = run(
            self.root, ["git", "rev-parse", f"{self.base}^{{tree}}"]
        ).stdout.strip()
        clean_tip = run(
            self.root,
            ["git", "commit-tree", clean_tree, "-p", hidden],
        ).stdout.strip()
        completed = run(
            self.root,
            ["git", "update-ref", self.branch_ref, clean_tip, self.base],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("histórico intermediário v2 não auditado", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base,
        )

    def hidden_v2_side_commit_with_clean_merge_tip(self) -> tuple[str, str]:
        """Return (hidden_bad, clean_tip) whose first-parent net tree is clean."""
        page = self.root / "data/editorial/v2_pages/base-01.jsonl"
        page.write_bytes(self.record("orphan-hidden-behind-clean-merge"))
        run(self.root, ["git", "add", str(page.relative_to(self.root))])
        bad_tree = run(self.root, ["git", "write-tree"]).stdout.strip()
        hidden = run(
            self.root,
            ["git", "commit-tree", bad_tree, "-p", self.base],
        ).stdout.strip()
        clean_tree = run(
            self.root, ["git", "rev-parse", f"{self.base}^{{tree}}"]
        ).stdout.strip()
        clean_tip = run(
            self.root,
            ["git", "commit-tree", clean_tree, "-p", self.base, "-p", hidden],
        ).stdout.strip()
        return hidden, clean_tip

    def test_ignored_tag_at_clean_tip_cannot_authorize_branch_creation(self) -> None:
        _hidden, clean_tip = self.hidden_v2_side_commit_with_clean_merge_tip()
        # Tag updates are outside this local branch hook boundary. They must
        # therefore never become an authority for a later branch update.
        run(self.root, ["git", "update-ref", "refs/tags/untrusted-clean", clean_tip])
        completed = run(
            self.root,
            ["git", "update-ref", "refs/heads/smuggled-clean-tag", clean_tip,
             "0" * 40],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("histórico intermediário v2 não auditado", completed.stderr)

    def test_ignored_tag_cannot_remove_hidden_commit_from_revision_walk(self) -> None:
        hidden, clean_tip = self.hidden_v2_side_commit_with_clean_merge_tip()
        # A tag at the hidden side commit does not `--contain` the merge tip,
        # but it used to poison `rev-list --not --all` and erase precisely the
        # commit that the hook had to inspect.
        run(self.root, ["git", "update-ref", "refs/tags/untrusted-hidden", hidden])
        completed = run(
            self.root,
            ["git", "update-ref", "refs/heads/smuggled-hidden-tag", clean_tip,
             "0" * 40],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("histórico intermediário v2 não auditado", completed.stderr)

    def test_detached_head_no_verify_still_runs_v2_gate(self) -> None:
        run(self.root, ["git", "checkout", "-q", "--detach", self.base])
        page = self.root / "data/editorial/v2_pages/base-01.jsonl"
        page.write_bytes(self.record("detached-orphan"))
        run(self.root, ["git", "add", str(page.relative_to(self.root))])
        completed = run(
            self.root,
            ["git", "commit", "--no-verify", "-m", "detached bad"],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn(
            "intent fora/ambiguo no portfolio candidato: "
            "data/editorial/v2_pages/base-01.jsonl:detached-orphan",
            completed.stderr)
        self.assertIn("COMO CORRIGIR", completed.stderr)
        self.assertIn("check-v2-portfolio-pairing", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base,
        )

    def test_v2_update_on_non_current_baseline_is_rejected(self) -> None:
        run(self.root, ["git", "branch", "side", self.base])
        base_tree = run(
            self.root, ["git", "rev-parse", f"{self.base}^{{tree}}"]
        ).stdout.strip()
        side_base = run(
            self.root,
            ["git", "commit-tree", base_tree, "-p", self.base],
        ).stdout.strip()
        run(
            self.root,
            ["git", "update-ref", "refs/heads/side", side_base, self.base],
        )
        portfolio = self.root / "data/editorial/portfolio_v2/base.jsonl"
        portfolio.write_bytes(
            self.record("baseline") + self.record("unused-prerequisite"))
        run(self.root, ["git", "add", str(portfolio.relative_to(self.root))])
        candidate_tree = run(self.root, ["git", "write-tree"]).stdout.strip()
        candidate = run(
            self.root,
            ["git", "commit-tree", candidate_tree, "-p", side_base],
        ).stdout.strip()
        completed = run(
            self.root,
            ["git", "update-ref", "refs/heads/side", candidate, side_base],
            check=False,
        )
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("ref não-current é insegura", completed.stderr)

    def test_explicit_hooks_path_override_is_outside_local_hook_boundary(self) -> None:
        self.prepare(["inside"], ["orphan"])
        completed = run(
            self.root,
            ["git", "-c", "core.hooksPath=/dev/null", "commit", "--no-verify",
             "-m", "documented local bypass"],
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotEqual(run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
                            self.base)

    def test_public_workflow_receipt_is_cooperative_not_authority(self) -> None:
        # This fixture deliberately manufactures the public identity and digest.
        # Passing proves compatibility/integrity only, never caller authority.
        target = self.prepare(["inside"], ["inside"])
        tree = run(self.root, ["git", "write-tree"]).stdout.strip()
        env = {
            "GIT_AUTHOR_NAME": "Portal Jurídico Workflow",
            "GIT_AUTHOR_EMAIL": "workflow-integrator@portal-juridico.invalid",
            "GIT_COMMITTER_NAME": "Portal Jurídico Workflow",
            "GIT_COMMITTER_EMAIL": "workflow-integrator@portal-juridico.invalid",
        }
        candidate = run(self.root, ["git", "commit-tree", tree, "-p", self.base],
                        env=env, check=True).stdout.strip()
        entry = run(self.root, ["git", "ls-tree", candidate, "--",
                                "data/editorial/v2_pages/area-01.jsonl"]).stdout
        mode, _kind, oid_and_path = entry.split(" ", 2)
        oid = oid_and_path.split("\t", 1)[0]
        digest = hashlib.sha256()
        digest.update(b"v2-finalized-reference-receipt-v1\0")
        digest.update(self.base.encode() + b"\0" + candidate.encode() + b"\0")
        digest.update(b"data/editorial/v2_pages/area-01.jsonl\0" +
                      mode.encode() + b"\0" + oid.encode() + b"\n")
        update_env = {
            "WIKI_V2_AUTHENTICATED_COMMIT_OID": candidate,
            "WIKI_V2_AUTHENTICATED_OLD_OID": self.base,
            "WIKI_V2_AUTHENTICATED_CLOSURE_KIND": "mass",
            "WIKI_V2_AUTHENTICATED_CLOSURE_SHA256": digest.hexdigest(),
        }
        promoted = run(
            self.root,
            ["git", "update-ref", self.branch_ref, candidate, self.base],
            env=update_env, check=False,
        )
        self.assertEqual(promoted.returncode, 0,
                         promoted.stdout + promoted.stderr)
        self.assertEqual(run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
                         candidate)
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o644)

    OPERATION = "portfolio-orphan-fixture-20260805"

    def install_quarantinable_shard(self) -> tuple[pathlib.Path, bytes]:
        """Land one finalized shard the sanctioned way, ready to be quarantined."""
        portfolio = self.root / "data/editorial/portfolio_v2/area.jsonl"
        portfolio.parent.mkdir(parents=True, exist_ok=True)
        portfolio.write_bytes(self.record("quarantinable"))
        run(self.root, ["git", "add", "data/editorial/portfolio_v2"])
        run(self.root, ["git", "commit", "-q", "-m", "portfolio prerequisite"])
        page = self.root / "data/editorial/v2_pages/area-01.jsonl"
        page.parent.mkdir(parents=True, exist_ok=True)
        payload = self.record("quarantinable")
        page.write_bytes(payload)
        run(self.root, ["git", "add", "data/editorial/v2_pages"])
        run(self.root, ["git", "commit", "-q", "-m", "finalized shard"])
        self.base = run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip()
        (self.root / "product-launcher-invocations").unlink(missing_ok=True)
        return page, payload

    def receipt_payload(self, payload: bytes, *, declared: bytes | None = None) -> bytes:
        """Recibo no formato do gerador sancionado (v2pageshardquarantine)."""
        digest = hashlib.sha256(declared if declared is not None else payload)
        digest_hex = digest.hexdigest()
        source = "data/editorial/v2_pages/area-01.jsonl"
        quarantine = (
            f"data/editorial/v2_pages_quarantine/{self.OPERATION}/"
            f"{digest_hex[:16]}-area-01.jsonl")
        return (json.dumps({
            "schema_version": 3,
            "operation_id": self.OPERATION,
            "status": "blocked_quarantined",
            "index_policy": "noindex",
            "render_allowed": False,
            "sitemap_allowed": False,
            "publication_allowed": False,
            "public": False,
            "indexable": False,
            "approval": False,
            "shards": [{
                "source_path": source,
                "quarantine_path": quarantine,
                "sha256": digest_hex,
                "mode": 420,
                "bytes": len(declared if declared is not None else payload),
                "intent_ids": ["quarantinable"],
                "reason_codes": ["portfolio_orphan"],
            }],
        }, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

    def stage_quarantine(
        self,
        *,
        with_receipt: bool = True,
        move_content: bool = True,
        tampered: bool = False,
    ) -> None:
        page, payload = self.install_quarantinable_shard()
        page.unlink()
        if move_content:
            digest_hex = hashlib.sha256(payload).hexdigest()
            destination = (
                self.root / "data/editorial/v2_pages_quarantine" /
                self.OPERATION / f"{digest_hex[:16]}-area-01.jsonl")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(
                self.record("tampered-after-receipt") if tampered else payload)
        if with_receipt:
            receipt = (
                self.root /
                "data/ops/v2_page_shard_quarantine_fixture_20260805.json")
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_bytes(self.receipt_payload(payload))
        run(self.root, ["git", "add", "-A", "data"])

    def test_quarantine_with_receipt_is_accepted(self) -> None:
        self.stage_quarantine()
        completed = run(
            self.root, ["git", "commit", "-m", "quarentena sancionada"],
            check=False)
        self.assertEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertNotEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base)
        self.assertEqual(len(self.launcher_invocations()), 1)
        surviving = run(
            self.root,
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--",
             "data/editorial/v2_pages"]).stdout.split()
        self.assertNotIn("data/editorial/v2_pages/area-01.jsonl", surviving)
        self.assertIn("data/editorial/v2_pages/base-01.jsonl", surviving)

    def test_removal_without_receipt_is_rejected(self) -> None:
        self.stage_quarantine(with_receipt=False)
        completed = run(
            self.root, ["git", "commit", "-m", "remoção casual"], check=False)
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("sem recibo de quarentena", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base)

    def test_removal_with_receipt_but_no_quarantined_content_is_rejected(self) -> None:
        self.stage_quarantine(move_content=False)
        completed = run(
            self.root, ["git", "commit", "-m", "recibo sem conteúdo"],
            check=False)
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("quarentena não confere com o recibo", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base)

    def test_quarantined_content_tampered_after_receipt_is_rejected(self) -> None:
        self.stage_quarantine(tampered=True)
        completed = run(
            self.root, ["git", "commit", "-m", "conteúdo trocado"], check=False)
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("quarentena não confere com o recibo", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base)

    def test_receipt_outside_candidate_tree_does_not_authorize_removal(self) -> None:
        """Recibo solto na worktree (untracked) não é autoridade de remoção."""
        self.stage_quarantine(with_receipt=False)
        page_payload = self.record("quarantinable")
        receipt = (
            self.root /
            "data/ops/v2_page_shard_quarantine_fixture_20260805.json")
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_bytes(self.receipt_payload(page_payload))
        completed = run(
            self.root, ["git", "commit", "-m", "recibo untracked"], check=False)
        self.assertNotEqual(
            completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("sem recibo de quarentena", completed.stderr)
        self.assertEqual(
            run(self.root, ["git", "rev-parse", "HEAD"]).stdout.strip(),
            self.base)


if __name__ == "__main__":
    unittest.main()
