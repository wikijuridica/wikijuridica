#!/usr/bin/env python3
import argparse
import hashlib
import importlib.metadata as metadata
import json
import pathlib
import subprocess
import sys
import time


RUFF_VERSION = "0.15.20"
PIP_AUDIT_VERSION = "2.10.1"
PIP_LICENSES_VERSION = "5.5.5"
MYPY_VERSION = "2.1.0"


def sha256_file(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def project_root(start: pathlib.Path) -> pathlib.Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    while current != current.parent:
        if (current / "go.mod").exists():
            return current
        current = current.parent
    raise SystemExit("python_quality_sca: go.mod not found")


def python_files(root: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for dirname in ("tools", "scripts"):
        base = root / dirname
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts or ".ruff_cache" in path.parts or ".mypy_cache" in path.parts:
                continue
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def requirement_files(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted((root / "tools").glob("requirements*.txt"), key=lambda p: p.relative_to(root).as_posix())


def inventory_hash(root: pathlib.Path, files: list[pathlib.Path]) -> tuple[int, int, int, str]:
    h = hashlib.sha256()
    line_count = 0
    byte_count = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        body = path.read_bytes()
        byte_count += len(body)
        if body:
            line_count += body.count(b"\n") + (0 if body.endswith(b"\n") else 1)
        h.update(rel.encode())
        h.update(b"\0")
        h.update(body)
        h.update(b"\0")
    return len(files), line_count, byte_count, "sha256:" + h.hexdigest()


def combined_hash(root: pathlib.Path, files: list[pathlib.Path]) -> str:
    h = hashlib.sha256()
    for path in files:
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def run_json(command: list[str], cwd: pathlib.Path, timeout: int, allow_findings: bool = False) -> tuple[int, str, str]:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        raise SystemExit(f"python_quality_sca: timeout command={' '.join(command)} timeout={timeout}s output={(stdout + stderr)[:1000]}")
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode not in (0, 1 if allow_findings else 0):
        raise SystemExit(f"python_quality_sca: command failed elapsed_ms={elapsed_ms} command={' '.join(command)} stdout={completed.stdout[:2000]} stderr={completed.stderr[:2000]}")
    return elapsed_ms, completed.stdout, completed.stderr


def run_text(command: list[str], cwd: pathlib.Path, timeout: int) -> str:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if completed.returncode != 0:
        raise SystemExit(f"python_quality_sca: command failed command={' '.join(command)} stdout={completed.stdout[:1000]} stderr={completed.stderr[:1000]}")
    return completed.stdout.strip()


def run_text_checked(command: list[str], cwd: pathlib.Path, timeout: int, allow_findings: bool = False) -> tuple[str, str]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    if completed.returncode not in (0, 1 if allow_findings else 0):
        raise SystemExit(f"python_quality_sca: command failed command={' '.join(command)} stdout={completed.stdout[:1000]} stderr={completed.stderr[:1000]}")
    return completed.stdout.strip(), completed.stderr.strip()


def tool_version(text: str, expected_name: str) -> str:
    parts = text.strip().split()
    if not parts:
        return ""
    if parts[0].lower().replace("_", "-") == expected_name:
        return parts[-1]
    return parts[-1]


def count_pip_audit_vulns(payload: dict) -> tuple[int, int]:
    dependencies = payload.get("dependencies") or []
    vulns = 0
    for dep in dependencies:
        vulns += len(dep.get("vulns") or [])
    return len(dependencies), vulns


def normalize_license(value: str) -> str:
    value = (value or "").strip()
    return value if value else "UNKNOWN"


def package_key(value: str) -> str:
    return (value or "").strip().lower().replace("_", "-")


def fingerprint(record: dict) -> str:
    copy = dict(record)
    copy["record_fingerprint_sha256"] = ""
    body = json.dumps(copy, ensure_ascii=False, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(body).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--checked-at", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ruff-timeout", type=int, default=60)
    parser.add_argument("--pip-audit-timeout", type=int, default=180)
    parser.add_argument("--pip-licenses-timeout", type=int, default=60)
    parser.add_argument("--mypy-timeout", type=int, default=120)
    args = parser.parse_args()

    root = project_root(pathlib.Path(args.root))
    bin_dir = pathlib.Path(sys.executable).parent
    ruff = str(bin_dir / "ruff")
    pip_audit = str(bin_dir / "pip-audit")
    pip_licenses = str(bin_dir / "pip-licenses")
    mypy = str(bin_dir / "mypy")
    req = root / "tools" / "requirements-python-quality-sca.txt"
    script = root / "tools" / "python_quality_sca_audit.py"

    py_files = python_files(root)
    req_files = requirement_files(root)
    py_count, line_count, byte_count, py_sha = inventory_hash(root, py_files)
    req_sha = combined_hash(root, req_files)

    ruff_version = tool_version(run_text([ruff, "--version"], root, 30), "ruff")
    pip_audit_version = tool_version(run_text([pip_audit, "--version"], root, 30), "pip-audit")
    pip_licenses_version = tool_version(run_text([pip_licenses, "--version"], root, 30), "pip-licenses")
    mypy_version = metadata.version("mypy")

    ruff_command = [ruff, "check", "--select", "E9,F63,F7,F82", "--output-format=json", "tools", "scripts"]
    _, ruff_stdout, _ = run_json(ruff_command, root, args.ruff_timeout, allow_findings=True)
    ruff_issues = json.loads(ruff_stdout or "[]")

    pip_audit_command = [pip_audit, "--local", "--format=json", "--progress-spinner=off"]
    _, pip_audit_stdout, _ = run_json(pip_audit_command, root, args.pip_audit_timeout, allow_findings=True)
    pip_audit_payload = json.loads(pip_audit_stdout or "{}")
    dependency_count, vulnerability_count = count_pip_audit_vulns(pip_audit_payload)

    pip_licenses_command = [pip_licenses, "--format=json"]
    _, pip_licenses_stdout, _ = run_json(pip_licenses_command, root, args.pip_licenses_timeout)
    licenses_payload = json.loads(pip_licenses_stdout or "[]")

    mypy_command = [mypy, "--ignore-missing-imports", "--follow-imports=silent", "--no-error-summary", "--no-pretty", "--show-error-codes", "tools", "scripts"]
    mypy_stdout, mypy_stderr = run_text_checked(mypy_command, root, args.mypy_timeout, allow_findings=True)
    mypy_lines = [line for line in (mypy_stdout + "\n" + mypy_stderr).splitlines() if line.strip()]
    packages = []
    seen_package_keys = set()
    for item in licenses_payload:
        name = item.get("Name") or item.get("name") or ""
        if package_key(name) in {"ruff", "pip-audit", "pip-licenses", "mypy"}:
            seen_package_keys.add(package_key(name))
            packages.append({
                "name": name,
                "version": item.get("Version") or item.get("version") or "",
                "license": normalize_license(item.get("License") or item.get("license") or ""),
            })
    for dist_name in ("ruff", "pip-audit", "pip-licenses", "mypy"):
        if dist_name in seen_package_keys:
            continue
        dist_meta = metadata.metadata(dist_name)
        packages.append({
            "name": dist_name,
            "version": metadata.version(dist_name),
            "license": normalize_license(dist_meta["License"] if "License" in dist_meta else ""),
        })
    packages = sorted(packages, key=lambda item: item["name"].lower())

    record = {
        "evidence_id": f"python-quality-sca-{args.checked_at}",
        "record_status": "python_quality_sca_blocked_no_publication",
        "checked_at": args.checked_at,
        "requirements_path": "tools/requirements-python-quality-sca.txt",
        "requirements_sha256": sha256_file(req),
        "tool_script_path": "tools/python_quality_sca_audit.py",
        "tool_script_sha256": sha256_file(script),
        "python_file_count": py_count,
        "python_line_count": line_count,
        "python_byte_count": byte_count,
        "python_inventory_sha256": py_sha,
        "requirement_file_count": len(req_files),
        "requirement_files_sha256": req_sha,
        "ruff_version": ruff_version,
        "ruff_command": ruff_command,
        "ruff_issue_count": len(ruff_issues),
        "pip_audit_version": pip_audit_version,
        "pip_audit_command": pip_audit_command,
        "pip_audit_vulnerability_count": vulnerability_count,
        "pip_audit_dependency_count": dependency_count,
        "pip_licenses_version": pip_licenses_version,
        "pip_licenses_command": pip_licenses_command,
        "pip_licenses_package_count": len(licenses_payload),
        "mypy_version": mypy_version,
        "mypy_command": mypy_command,
        "mypy_issue_count": len(mypy_lines),
        "toolchain_packages": packages,
        "scale_path": "python_tooling_all_scripts_and_pinned_requirements_10k_100k_1m_factory",
        "use_policy": "blocked_python_quality_sca_no_publication",
        "publication_allowed": False,
        "render_allowed": False,
        "sitemap_allowed": False,
        "public_path": "",
        "approval": False,
        "index_policy": "noindex",
        "no_public_artifacts_touched": True,
        "license_contents_stored": False,
        "raw_external_text_stored": False,
        "record_fingerprint_sha256": "",
    }
    record["record_fingerprint_sha256"] = fingerprint(record)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"python-quality-sca: wrote {args.output} python_files={py_count} ruff_issues={len(ruff_issues)} vulnerabilities={vulnerability_count} packages={len(packages)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
