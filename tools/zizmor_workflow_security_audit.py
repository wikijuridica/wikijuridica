#!/usr/bin/env python3
import argparse
import json
import pathlib
import subprocess
import sys


def project_root(start: pathlib.Path) -> pathlib.Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    while current != current.parent:
        if (current / "go.mod").exists():
            return current
        current = current.parent
    raise SystemExit("zizmor_workflow_security: go.mod not found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--zizmor-bin", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    root = project_root(pathlib.Path(args.root))
    output = pathlib.Path(args.output)
    command = [
        args.zizmor_bin,
        "--offline",
        "--format=json",
        "--no-exit-codes",
        "--no-progress",
        "--collect=workflows",
        "--strict-collection",
        ".github/workflows",
        ".github/dependabot.yml",
    ]
    try:
        completed = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=args.timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        raise SystemExit(f"zizmor_workflow_security: timeout output={(stdout + stderr)[:1000]}")
    if completed.returncode != 0:
        raise SystemExit(
            "zizmor_workflow_security: command failed "
            f"code={completed.returncode} stdout={completed.stdout[:1000]} stderr={completed.stderr[:1000]}"
        )
    payload = json.loads(completed.stdout or "[]")
    if not isinstance(payload, list):
        raise SystemExit("zizmor_workflow_security: JSON output must be a list")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
