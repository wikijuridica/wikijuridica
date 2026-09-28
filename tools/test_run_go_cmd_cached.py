#!/usr/bin/env python3
"""Focused behavioral tests for bootstrap-safe cached Go binaries."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import unittest


RUNNER_SOURCE = pathlib.Path(__file__).with_name("run-go-cmd-cached")
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAVY_SUPPORT = (
    "run-heavy-throttled",
    "supervise-process-tree",
    "check-command-progress",
    "run-heavy-progress-watchdog",
)


# 2026-09-05: run-go-cmd-cached gained (2026-08-29) a fast binary-identity path
# for the default/non-bootstrap cache mode: instead of a full sha256 of the
# cached command binary (expensive on real ~240MB `cmd/*` binaries), it reads
# the binary as ELF64 and authenticates the Go linker's own `.note.go.buildid`
# note (see go_build_id() at run-go-cmd-cached:1908 and again at the pre-exec
# pin at :3690). A real `go build` on this host ALWAYS produces that; nothing
# in production ever hands this code a non-ELF file, so the check is correct
# and must not be loosened. But FAKE_GO_MODERN below used to fake the
# "compiled" cmd/example binary as a literal bash script (`#!/usr/bin/env
# bash...`), which is not ELF at all -- every test going through the
# non-bootstrap path failed with "unsupported binary format for fast
# identity". The fixture, not the product, was stale.
#
# Fix: compile ONE tiny real Go binary (this source) via the repo's own
# tools/go-modern, ONCE per test process (see setUpModule), and have
# FAKE_GO_MODERN's `build)` case install a COPY of it (never a fresh compile
# per test -- that would reintroduce real compilation into 57 tests) as the
# "cmd/example" output, with the one piece of build-time-frozen state
# (source_sha256, which mutation tests rely on staying fixed even after the
# source file changes post-build) appended as trailing bytes after the
# legitimate ELF content. Appending bytes past everything the ELF section
# header table points to does not affect go_build_id() (it only reads the
# byte ranges the section table names) nor the kernel's ELF loader (verified
# with readelf + the exact identity heredoc from run-go-cmd-cached before
# wiring this in). Bytes actually read at RUN TIME (metadata sha256, cwd, the
# optional fd/SIGTERM probes) are read live via os.Getenv/os.Getwd, exactly
# matching what the old bash script did when IT executed -- no need to freeze
# those at build time.
FAKE_BINARY_HELPER_GO = r'''package main

import (
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

// Trailing marker appended by FAKE_GO_MODERN's `build)` case after copying
// this compiled template into place. Fixed-length payload (a hex sha256 is
// always 64 chars), so every installed "binary" has a deterministic size.
const beginMarker = "#WIKI_FAKE_BINARY_SOURCE_SHA256#"
const endMarker = "#END#"

func readTail(path string, max int64) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil {
		return nil, err
	}
	size := info.Size()
	start := int64(0)
	if size > max {
		start = size - max
	}
	buf := make([]byte, size-start)
	if _, err := f.ReadAt(buf, start); err != nil {
		return nil, err
	}
	return buf, nil
}

func main() {
	// source_sha256 is frozen at "build" time (baked into the file this
	// process IS), not re-read from the live source tree -- tests mutate
	// cmd/example/main.go AFTER building and expect the cached binary to
	// keep reporting the OLD hash.
	if self, err := os.Executable(); err == nil {
		if tail, err := readTail(self, 4096); err == nil {
			text := string(tail)
			if i := strings.LastIndex(text, beginMarker); i >= 0 {
				rest := text[i+len(beginMarker):]
				if j := strings.Index(rest, endMarker); j >= 0 {
					fmt.Printf("source=%s\n", rest[:j])
				}
			}
		}
	}
	fmt.Printf("metadata=%s\n", os.Getenv("WIKI_GO_CMD_BINARY_METADATA_SHA256"))
	if pwd, err := os.Getwd(); err == nil {
		fmt.Printf("runtime_pwd=%s\n", pwd)
	}
	if fdSpec := os.Getenv("FAKE_BINARY_REQUIRE_FD"); fdSpec != "" {
		if _, err := os.Stat("/proc/self/fd/" + fdSpec); err != nil {
			fmt.Fprintf(os.Stderr, "missing inherited fd %s\n", fdSpec)
			os.Exit(70)
		}
	}
	if os.Getenv("FAKE_BINARY_IGNORE_TERM") == "1" {
		signal.Ignore(syscall.SIGTERM)
		for {
			time.Sleep(50 * time.Millisecond)
		}
	}
}
'''


FAKE_GO_MODERN = r'''#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "${1:-}" in
version)
	printf 'go version %s %s/%s\n' "${FAKE_GOVERSION:-go1.99.1}" "${FAKE_GOOS:-linux}" "${FAKE_GOARCH:-amd64}"
	;;
env)
	if [[ -n "${FAKE_GO_ENV_CALL_COUNT_PATH:-}" ]]; then
		env_call_count=0
		if [[ -s "$FAKE_GO_ENV_CALL_COUNT_PATH" ]]; then
			env_call_count="$(sed -n '1p' "$FAKE_GO_ENV_CALL_COUNT_PATH")"
		fi
		env_call_count=$((env_call_count + 1))
		printf '%s\n' "$env_call_count" >"$FAKE_GO_ENV_CALL_COUNT_PATH"
		if [[ "$env_call_count" == "${MUTATE_SOURCE_ON_GO_ENV_CALL:-never}" ]]; then
			printf '%s\n' '// changed between cache selection and exec' >>"$PWD/cmd/example/main.go"
		fi
	fi
	printf '{"AR":"%s","CC":"%s","CGO_CFLAGS":"%s","CGO_CPPFLAGS":"","CGO_CXXFLAGS":"-O2 -g","CGO_ENABLED":"%s","CGO_FFLAGS":"-O2 -g","CGO_LDFLAGS":"-O2 -g","CXX":"%s","GO386":"%s","GOAMD64":"v1","GOARCH":"%s","GOARM64":"","GOENV":"%s/fake-go-env","GOEXPERIMENT":"%s","GOFLAGS":"%s","GOMOD":"%s/go.mod","GOMODCACHE":"%s/fake-mod-cache","GOOS":"%s","GOROOT":"%s/fake-go-root","GOTOOLCHAIN":"%s","GOVERSION":"%s","GOWORK":"","PKG_CONFIG":"%s"}\n' \
		"${FAKE_AR:-ar}" "${FAKE_CC:-gcc}" "${FAKE_CGO_CFLAGS:--O2 -g}" "${FAKE_CGO_ENABLED:-0}" "${FAKE_CXX:-g++}" "${FAKE_GO386:-}" "${FAKE_GOARCH:-amd64}" "$ROOT" "${FAKE_GOEXPERIMENT:-}" "${FAKE_GOFLAGS:-}" "$PWD" "$ROOT" "${FAKE_GOOS:-linux}" "$ROOT" "${FAKE_GOTOOLCHAIN:-local}" "${FAKE_GOVERSION:-go1.99.1}" "${FAKE_PKG_CONFIG:-pkg-config}"
	;;
list)
	case " $* " in
	*' -json '*)
		printf '{"Dir":"%s/cmd/example","GoFiles":["main.go"],"ImportPath":"example/cmd/example","Module":{"GoMod":"%s/go.mod","Main":true,"Path":"example"}}\n' "$PWD" "$PWD"
		;;
	*)
		printf '%s/cmd/example\n' "$PWD"
		;;
	esac
	;;
build)
	case " $* " in
	*' -tags devcmds '*) ;;
	*)
		printf '%s\n' 'fake go-modern: missing -tags devcmds' >&2
		exit 64
		;;
	esac
	shift
	output=""
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-o)
			output="$2"
			shift 2
			;;
		*) shift ;;
		esac
	done
	[[ -n "$output" ]]
	source_sha256="$(sha256sum "$PWD/cmd/example/main.go" | awk '{print $1}')"
	build_count=0
	if [[ -s "${BUILD_COUNT_PATH:?}" ]]; then
		build_count="$(sed -n '1p' "$BUILD_COUNT_PATH")"
	fi
	printf '%s\n' "$((build_count + 1))" >"$BUILD_COUNT_PATH"
	if [[ "${FAKE_BUILD_IGNORE_TERM:-}" == "1" ]]; then
		trap : TERM
		while :; do sleep 0.05 || :; done
	fi
	# 2026-09-05: the "binary" must be real ELF64 with a Go build-id note --
	# run-go-cmd-cached's fast identity path parses it as such (see the
	# comment above FAKE_BINARY_HELPER_GO). FAKE_BINARY_TEMPLATE is a
	# precompiled copy of that helper, installed ONCE per test process by
	# setUpModule; here we just install a COPY and append the one piece of
	# state that must be frozen at "build" time. FAKE_BINARY_REQUIRE_FD and
	# FAKE_BINARY_IGNORE_TERM are read directly by the helper at RUN time
	# (os.Getenv), so nothing about them needs to be embedded here.
	: "${FAKE_BINARY_TEMPLATE:?FAKE_BINARY_TEMPLATE must point at a precompiled real-ELF fake binary}"
	cp -- "$FAKE_BINARY_TEMPLATE" "$output"
	chmod u+w -- "$output"
	printf '\n#WIKI_FAKE_BINARY_SOURCE_SHA256#%s#END#\n' "$source_sha256" >>"$output"
	chmod 0755 "$output"
	if [[ "${MUTATE_SOURCE_AFTER_BUILD:-}" == "1" ]]; then
		printf '%s\n' '// changed during build' >>"$PWD/cmd/example/main.go"
	fi
	;;
*)
	printf 'fake go-modern: unsupported command %s\n' "${1:-}" >&2
	exit 64
	;;
esac
'''


_fake_binary_template_dir: tempfile.TemporaryDirectory[str] | None = None
FAKE_BINARY_TEMPLATE_PATH: pathlib.Path | None = None


def setUpModule() -> None:
    """Compiles FAKE_BINARY_HELPER_GO exactly ONCE for the whole test process.

    Deliberately OUTSIDE any test's self.root: self.root/go.mod declares
    `go 1.99` for the FAKE go-modern's own `env` output (FAKE_GOVERSION
    etc.), and a real `go` invoked there under GOTOOLCHAIN=auto would try to
    DOWNLOAD go1.99 -- network, forbidden, and it would hang. This uses the
    repo's own tools/go-modern (which resolves the toolchain pinned in the
    real go.mod, go1.26.6) against an unrelated scratch module that declares
    a real, already-installed version.
    """
    global _fake_binary_template_dir, FAKE_BINARY_TEMPLATE_PATH
    _fake_binary_template_dir = tempfile.TemporaryDirectory(
        prefix="run-go-cmd-cached-fake-binary-"
    )
    scratch = pathlib.Path(_fake_binary_template_dir.name)
    (scratch / "go.mod").write_text("module fakebinary\n\ngo 1.26\n", encoding="utf-8")
    (scratch / "main.go").write_text(FAKE_BINARY_HELPER_GO, encoding="utf-8")
    template = scratch / "fake-binary-template"
    go_modern = REPO_ROOT / "tools" / "go-modern"
    environment = os.environ.copy()
    environment.update(
        {
            "GOTOOLCHAIN": "local",
            "GOFLAGS": "",
            "GOWORK": "off",
            "GOCACHE": os.fspath(scratch / "gocache"),
            "GOENV": os.fspath(scratch / "goenv"),
        }
    )
    result = subprocess.run(
        [os.fspath(go_modern), "build", "-buildvcs=false", "-o", os.fspath(template), "."],
        cwd=scratch,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or not template.is_file():
        _fake_binary_template_dir.cleanup()
        _fake_binary_template_dir = None
        raise RuntimeError(
            "setUpModule: failed to compile the real-ELF fake-binary template "
            f"via {go_modern}: exit={result.returncode}\n{result.stderr}"
        )
    FAKE_BINARY_TEMPLATE_PATH = template


def tearDownModule() -> None:
    if _fake_binary_template_dir is not None:
        _fake_binary_template_dir.cleanup()


class RunGoCmdCachedTest(unittest.TestCase):
    def setUp(self) -> None:
        # 2026-07-31: WIKI_TEST_FIXTURE_ROOT permite rodar a suite fora de /tmp.
        # E necessario em dois casos reais: (a) sandbox onde /tmp pertence ao uid
        # de overflow com mode 1777 e o wrapper -- corretamente -- recusa cache
        # cujo ancestral outro usuario pode trocar; (b) validar o lock em mount
        # que nega DELETE, que e onde o bug de lock orfao aparece.
        self.temporary = tempfile.TemporaryDirectory(
            prefix="run-go-cmd-cached-test-",
            dir=os.environ.get("WIKI_TEST_FIXTURE_ROOT") or None,
        )
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "tools").mkdir()
        (self.root / "cmd" / "example").mkdir(parents=True)
        (self.root / "internal").mkdir()
        (self.root / "home").mkdir()
        (self.root / "fake-go-root" / "bin").mkdir(parents=True)
        shutil.copy2(RUNNER_SOURCE, self.root / "tools" / "run-go-cmd-cached")
        go_modern = self.root / "tools" / "go-modern"
        go_modern.write_text(FAKE_GO_MODERN, encoding="utf-8")
        go_modern.chmod(0o755)
        fake_go = self.root / "fake-go-root" / "bin" / "go"
        fake_go.write_text("fake authenticated Go toolchain\n", encoding="utf-8")
        fake_go.chmod(0o755)
        (self.root / "go.mod").write_text("module example\n\ngo 1.99\n", encoding="utf-8")
        (self.root / "go.sum").write_text("", encoding="utf-8")
        self.source = self.root / "cmd" / "example" / "main.go"
        self.source.write_text("package main\nfunc main() { println(1) }\n", encoding="utf-8")
        self.cache = self.root / "cache"
        self.build_count_path = self.root / "build-count"

    def tearDown(self) -> None:
        try:
            self.temporary.cleanup()
        except (OSError, RecursionError):
            # 2026-07-31: em mount que nega DELETE (sandbox Cowork/virtiofs) o
            # fixture nao pode ser removido. Isso e propriedade do sistema de
            # arquivos, nao falha do comportamento sob teste -- e e exatamente
            # nesse mount que os testes de lock precisam rodar.
            pass

    @staticmethod
    def contract_for(payload: bytes) -> str:
        return "sha256:" + hashlib.sha256(b"test-source-contract/v1\0" + payload).hexdigest()

    def environment(
        self,
        source_contract: str | None,
        build_source_root: pathlib.Path | None = None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": os.fspath(self.root / "tools") + os.pathsep + environment.get("PATH", ""),
                "BUILD_COUNT_PATH": os.fspath(self.build_count_path),
                "FAKE_BINARY_TEMPLATE": os.fspath(FAKE_BINARY_TEMPLATE_PATH),
                "GOCACHE": os.fspath(self.root / "gocache"),
                "HOME": os.fspath(self.root / "home"),
                "WIKI_GO_CMD_BIN_CACHE": os.fspath(self.cache),
                "WIKI_GO_CMD_BUILD_BUDGET_MS": "5000",
                "WIKI_GO_CMD_BUILD_IDENTITY_TIMEOUT_SECONDS": "3",
                "WIKI_GO_CMD_DEPENDENCY_LIST_TIMEOUT_SECONDS": "3",
                "WIKI_GO_CMD_METADATA_TIMEOUT_SECONDS": "3",
                "WIKI_GO_CMD_TIMEOUT_SECONDS": "3",
            }
        )
        environment.pop("WIKI_BOOTSTRAP_SOURCE_CONTRACT_SHA256", None)
        environment.pop("WIKI_GO_CMD_BUILD_SOURCE_ROOT", None)
        environment.pop("WIKI_RUN_GO_CMD_CACHED_UNDER_TIMEOUT", None)
        environment.pop("MUTATE_SOURCE_AFTER_BUILD", None)
        environment.pop("FAKE_BINARY_IGNORE_TERM", None)
        environment.pop("FAKE_BUILD_IGNORE_TERM", None)
        if source_contract is not None:
            environment["WIKI_BOOTSTRAP_SOURCE_CONTRACT_SHA256"] = source_contract
        if build_source_root is not None:
            environment["WIKI_GO_CMD_BUILD_SOURCE_ROOT"] = os.fspath(build_source_root)
        if extra:
            environment.update(extra)
        return environment

    def run_cached(
        self,
        source_contract: str | None,
        build_source_root: pathlib.Path | None = None,
        extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(source_contract, build_source_root, extra),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def build_count(self) -> int:
        return int(self.build_count_path.read_text(encoding="ascii").strip())

    def binary(self) -> pathlib.Path:
        return self.cache / "example" / "example"

    def metadata(self) -> pathlib.Path:
        return self.cache / "example" / "bootstrap-build-metadata.json"

    def identity(self) -> pathlib.Path:
        return self.cache / "example" / "build-identity.json"

    def test_source_contract_change_rebuilds_when_source_mtime_is_preserved(self) -> None:
        first_bytes = self.source.read_bytes()
        first = self.run_cached(self.contract_for(first_bytes))
        self.assertEqual(self.build_count(), 1)
        self.assertIn("bootstrap_binary_metadata schema=", first.stderr)

        metadata_path = self.metadata()
        payload = metadata_path.read_bytes()
        record = json.loads(payload)
        digest = "sha256:" + hashlib.sha256(payload).hexdigest()
        self.assertEqual(record["schema"], "run-go-cmd-cached-build-metadata/v1")
        self.assertEqual(record["build_context"]["package"], "./cmd/example")
        self.assertEqual(
            record["build_context"]["build_flags"],
            ["-tags", "devcmds", "-buildvcs=false"],
        )
        self.assertEqual(record["build_context"]["go_version"], "go version go1.99.1 linux/amd64")
        self.assertRegex(record["build_context"]["cache_runner"]["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertTrue(record["build_context"]["dependency_closure"]["entries"])
        self.assertEqual(
            (self.cache / "example" / "bootstrap-build-metadata.sha256").read_text(encoding="ascii").strip(),
            digest,
        )
        self.assertEqual(
            (self.cache / "example" / "bootstrap-build-metadata.d" / f"{digest[7:]}.json").read_bytes(),
            payload,
        )
        self.assertIn(f"metadata={digest}", first.stdout)

        original_stat = self.source.stat()
        second_bytes = b"package main\nfunc main() { println(2) }\n"
        self.assertEqual(len(first_bytes), len(second_bytes))
        self.source.write_bytes(second_bytes)
        os.utime(
            self.source,
            ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
        )
        self.assertEqual(self.source.stat().st_mtime_ns, original_stat.st_mtime_ns)

        second = self.run_cached(self.contract_for(second_bytes))
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(second.stderr.count("build_start command=./cmd/example"), 1)
        self.assertIn(hashlib.sha256(second_bytes).hexdigest(), second.stdout)

        third = self.run_cached(self.contract_for(second_bytes))
        self.assertEqual(self.build_count(), 2)
        self.assertNotIn("build_start command=./cmd/example", third.stderr)

    def test_tampered_binary_forces_one_rebuild(self) -> None:
        source_contract = self.contract_for(self.source.read_bytes())
        self.run_cached(source_contract)
        # run-go-cmd-cached:3938 installs every cached binary at 0500 (no
        # write bit at all, even for the owner) -- a real hardening, not a
        # bug (it normalizes the mode mktemp+`go build -o` leaves behind in
        # sandboxes that deny unlink; see the comment there). Tampering the
        # bytes to simulate corruption needs write access; as the file's
        # OWNER we can always grant that to ourselves (chmod 0500 defends
        # against OTHER users/processes, never against the owning process --
        # see the threat model in run-go-cmd-cached's binary_identity()
        # comment block). Restore 0500 after so the tamper is
        # indistinguishable from silent byte corruption, which is what this
        # test claims to simulate; leaving it writable could make the
        # bootstrap validator fail on MODE instead of on fingerprint.
        os.chmod(self.binary(), 0o700)
        with self.binary().open("ab") as binary:
            binary.write(b"\n# tampered\n")
        os.chmod(self.binary(), 0o500)

        result = self.run_cached(source_contract)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertIn("binary fingerprint mismatch", result.stderr)
        record = json.loads(self.metadata().read_text(encoding="utf-8"))
        observed = "sha256:" + hashlib.sha256(self.binary().read_bytes()).hexdigest()
        self.assertEqual(record["binary"]["sha256"], observed)

    def test_source_contract_token_change_alone_forces_one_rebuild(self) -> None:
        first_contract = self.contract_for(b"contract-a")
        second_contract = self.contract_for(b"contract-b")
        self.run_cached(first_contract)

        result = self.run_cached(second_contract)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        record = json.loads(self.metadata().read_text(encoding="utf-8"))
        self.assertEqual(record["build_context"]["source_contract_sha256"], second_contract)

    def test_real_build_source_digest_rebuilds_even_with_stale_environment_contract(self) -> None:
        stale_contract = self.contract_for(self.source.read_bytes())
        self.run_cached(stale_contract)
        first_source_digest = json.loads(self.metadata().read_text(encoding="utf-8"))["build_context"]["build_source"]["sha256"]
        original_stat = self.source.stat()
        changed = b"package main\nfunc main() { println(4) }\n"
        self.source.write_bytes(changed)
        os.utime(self.source, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

        result = self.run_cached(stale_contract)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        second_source_digest = json.loads(self.metadata().read_text(encoding="utf-8"))["build_context"]["build_source"]["sha256"]
        self.assertNotEqual(first_source_digest, second_source_digest)
        self.assertIn(hashlib.sha256(changed).hexdigest(), result.stdout)

    def test_stale_metadata_forces_one_rebuild(self) -> None:
        source_contract = self.contract_for(self.source.read_bytes())
        self.run_cached(source_contract)
        record = json.loads(self.metadata().read_text(encoding="utf-8"))
        record["build_context"]["source_contract_sha256"] = "sha256:" + "f" * 64
        self.metadata().write_text(
            json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

        result = self.run_cached(source_contract)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertIn("build context mismatch", result.stderr)

    def test_missing_metadata_rebuilds_an_existing_non_bootstrap_binary_once(self) -> None:
        self.run_cached(None)
        self.assertTrue(self.binary().exists())
        self.assertFalse(self.metadata().exists())

        result = self.run_cached(self.contract_for(self.source.read_bytes()))
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertTrue(self.metadata().exists())

    def test_non_bootstrap_fast_path_rebuilds_when_source_mtime_is_preserved(self) -> None:
        first = self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        self.assertNotIn("bootstrap_binary_metadata", first.stderr)
        self.assertFalse(self.metadata().exists())
        identity = json.loads(self.identity().read_text(encoding="utf-8"))
        self.assertEqual(identity["schema"], "run-go-cmd-cached-fast-build-context/v1")
        self.assertEqual(identity["build_flags"], ["-tags", "devcmds", "-buildvcs=false"])
        self.assertEqual(identity["go_toolchain"]["CGO_ENABLED"], "0")
        self.assertRegex(identity["go_toolchain_binary"]["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(identity["go_modern"]["sha256"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(identity["cache_runner"]["sha256"], r"^sha256:[0-9a-f]{64}$")

        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        original = self.source.stat()
        changed = b"package main\nfunc main() { println(3) }\n"
        self.assertEqual(len(changed), self.source.stat().st_size)
        self.source.write_bytes(changed)
        os.utime(self.source, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.assertEqual(self.source.stat().st_mtime_ns, original.st_mtime_ns)

        rebuilt = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(rebuilt.stderr.count("build_start command=./cmd/example"), 1)
        self.assertIn(hashlib.sha256(changed).hexdigest(), rebuilt.stdout)

    def test_non_bootstrap_content_identity_beats_newer_restored_cache_timestamps(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        original = self.source.stat()
        changed = b"package main\nfunc main() { println(7) }\n"
        self.assertEqual(len(changed), original.st_size)
        self.source.write_bytes(changed)
        os.utime(self.source, ns=(original.st_atime_ns, original.st_mtime_ns))
        future = time.time_ns() + 2_000_000_000
        for cache_path in (self.binary(), self.identity(), self.cache / "example" / "build-binary.sha256"):
            os.utime(cache_path, ns=(future, future))

        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertIn(hashlib.sha256(changed).hexdigest(), result.stdout)

    def test_non_bootstrap_go_mod_and_nested_embed_inputs_are_content_addressed(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        go_mod = self.root / "go.mod"
        original_mod = go_mod.stat()
        changed_mod = go_mod.read_bytes().replace(b"go 1.99", b"go 1.98")
        go_mod.write_bytes(changed_mod)
        os.utime(go_mod, ns=(original_mod.st_atime_ns, original_mod.st_mtime_ns))
        self.run_cached(None)
        self.assertEqual(self.build_count(), 2)

        nested = self.root / "cmd" / "example" / "assets" / "nested.txt"
        nested.parent.mkdir()
        nested.write_text("embedded input v1\n", encoding="utf-8")
        self.run_cached(None)
        self.assertEqual(self.build_count(), 3)
        original_nested = nested.stat()
        nested.write_text("embedded input v2\n", encoding="utf-8")
        os.utime(nested, ns=(original_nested.st_atime_ns, original_nested.st_mtime_ns))
        self.run_cached(None)
        self.assertEqual(self.build_count(), 4)

    def test_non_bootstrap_tampered_binary_digest_forces_rebuild(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        # See the identical comment in test_tampered_binary_forces_one_rebuild:
        # the cached binary is installed 0500 (run-go-cmd-cached:3938); as the
        # owner we grant ourselves write access to simulate corruption, then
        # restore 0500 so the tamper looks like silent byte corruption.
        os.chmod(self.binary(), 0o700)
        with self.binary().open("ab") as binary:
            binary.write(b"\n# tampered fast cache\n")
        os.chmod(self.binary(), 0o500)

        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)

    def test_non_bootstrap_identity_changes_rebuild_for_build_semantics(self) -> None:
        build_environment: dict[str, str] = {}
        self.run_cached(None, extra=build_environment)
        self.assertEqual(self.build_count(), 1)

        changes = [
            ("FAKE_CGO_ENABLED", "1", "CGO_ENABLED"),
            ("FAKE_GOFLAGS", "-trimpath", "GOFLAGS"),
            ("FAKE_GOOS", "freebsd", "GOOS"),
            ("FAKE_GO386", "softfloat", "GO386"),
            ("FAKE_GOARCH", "arm64", "GOARCH"),
            ("FAKE_GOEXPERIMENT", "loopvar", "GOEXPERIMENT"),
            ("FAKE_GOTOOLCHAIN", "go1.99.2", "GOTOOLCHAIN"),
            ("FAKE_GOVERSION", "go1.99.2", "GOVERSION"),
        ]
        for expected_build_count, (environment_name, value, go_env_name) in enumerate(changes, start=2):
            with self.subTest(environment_name=environment_name):
                build_environment[environment_name] = value
                result = self.run_cached(None, extra=build_environment)
                self.assertEqual(self.build_count(), expected_build_count)
                self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
                identity = json.loads(self.identity().read_text(encoding="utf-8"))
                self.assertEqual(identity["go_toolchain"][go_env_name], value)

    def test_non_bootstrap_identity_hashes_toolchain_binary_and_go_modern_wrapper(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)

        fake_go = self.root / "fake-go-root" / "bin" / "go"
        original_go_stat = fake_go.stat()
        fake_go.write_bytes(fake_go.read_bytes() + b"toolchain identity changed\n")
        os.utime(fake_go, ns=(original_go_stat.st_atime_ns, original_go_stat.st_mtime_ns))
        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)

        go_modern = self.root / "tools" / "go-modern"
        original_wrapper_stat = go_modern.stat()
        go_modern.write_bytes(go_modern.read_bytes() + b"\n# wrapper identity changed\n")
        os.utime(go_modern, ns=(original_wrapper_stat.st_atime_ns, original_wrapper_stat.st_mtime_ns))
        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 3)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)

        runner = self.root / "tools" / "run-go-cmd-cached"
        original_runner_stat = runner.stat()
        runner.write_bytes(runner.read_bytes() + b"\n# cache runner identity changed\n")
        os.utime(runner, ns=(original_runner_stat.st_atime_ns, original_runner_stat.st_mtime_ns))
        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 4)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)

    def test_non_bootstrap_cgo_compiler_binary_is_content_addressed(self) -> None:
        compiler = self.root / "tools" / "fake-cc"
        compiler.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        compiler.chmod(0o755)
        environment = {"FAKE_CGO_ENABLED": "1", "FAKE_CC": "fake-cc"}
        self.run_cached(None, extra=environment)
        self.assertEqual(self.build_count(), 1)
        identity = json.loads(self.identity().read_text(encoding="utf-8"))
        cc_identity = next(
            tool for tool in identity["cgo_build_tools"] if tool["environment"] == "CC"
        )
        self.assertEqual(cc_identity["path"], os.fspath(compiler))
        self.assertRegex(cc_identity["sha256"], r"^sha256:[0-9a-f]{64}$")

        original = compiler.stat()
        compiler.write_bytes(compiler.read_bytes() + b"# changed compiler bytes\n")
        os.utime(compiler, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.run_cached(None, extra=environment)
        self.assertEqual(self.build_count(), 2)

    def test_bootstrap_cgo_compiler_binary_is_content_addressed(self) -> None:
        compiler = self.root / "tools" / "fake-cc"
        compiler.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        compiler.chmod(0o755)
        environment = {"FAKE_CGO_ENABLED": "1", "FAKE_CC": "fake-cc"}
        source_contract = self.contract_for(self.source.read_bytes())
        self.run_cached(source_contract, extra=environment)
        self.assertEqual(self.build_count(), 1)
        record = json.loads(self.metadata().read_text(encoding="utf-8"))
        cc_identity = next(
            tool
            for tool in record["build_context"]["cgo_build_tools"]
            if tool["environment"] == "CC"
        )
        self.assertEqual(cc_identity["path"], os.fspath(compiler))

        original = compiler.stat()
        compiler.write_bytes(compiler.read_bytes() + b"# changed compiler bytes\n")
        os.utime(compiler, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.run_cached(source_contract, extra=environment)
        self.assertEqual(self.build_count(), 2)

    def test_non_bootstrap_local_replace_fails_closed_before_build(self) -> None:
        (self.root / "go.mod").write_text(
            "module example\n\ngo 1.99\n\nreplace example/local => ../local-module\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("local go.mod replace requires authenticated bootstrap cache mode", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_non_bootstrap_cache_without_identity_is_rebuilt_once(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        self.identity().unlink()

        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertTrue(self.identity().is_file())

        self.run_cached(None)
        self.assertEqual(self.build_count(), 2)

    def test_non_bootstrap_fifo_digest_identity_is_rebuilt_without_blocking(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        digest_identity = self.cache / "example" / "build-binary.sha256"
        digest_identity.unlink()
        os.mkfifo(digest_identity, 0o600)

        started = time.monotonic()
        result = self.run_cached(None)
        elapsed = time.monotonic() - started

        self.assertEqual(self.build_count(), 2)
        self.assertIn("source=", result.stdout)
        self.assertTrue(stat.S_ISREG(digest_identity.lstat().st_mode))
        self.assertLess(elapsed, 10.0)

    def test_non_bootstrap_cached_binary_symlink_is_rebuilt_not_executed(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        redirected = self.cache / "redirected-example"
        self.binary().rename(redirected)
        self.binary().symlink_to(redirected)

        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertTrue(self.binary().is_file())
        self.assertFalse(self.binary().is_symlink())

    def test_cached_binary_symlink_to_directory_cannot_redirect_build_output(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        displaced = self.cache / "displaced-example"
        self.binary().rename(displaced)
        outside = self.root / "outside-cache-target"
        outside.mkdir()
        self.binary().symlink_to(outside, target_is_directory=True)

        result = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertEqual(result.stderr.count("build_start command=./cmd/example"), 1)
        self.assertTrue(self.binary().is_file())
        self.assertFalse(self.binary().is_symlink())
        self.assertEqual(list(outside.iterdir()), [])

    def test_cached_binary_fifo_is_atomically_replaced_without_blocking(self) -> None:
        self.binary().parent.mkdir(parents=True)
        os.mkfifo(self.binary(), 0o600)

        started = time.monotonic()
        result = self.run_cached(None)
        elapsed = time.monotonic() - started

        self.assertEqual(self.build_count(), 1)
        self.assertIn("source=", result.stdout)
        self.assertTrue(stat.S_ISREG(self.binary().lstat().st_mode))
        self.assertLess(elapsed, 10.0)
        self.assertFalse((self.cache / "example" / "build.lock").exists())

    def test_cached_binary_directory_fails_closed_without_writing_inside_it(self) -> None:
        self.binary().mkdir(parents=True)
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        elapsed = time.monotonic() - started

        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertTrue(self.binary().is_dir())
        self.assertEqual(list(self.binary().iterdir()), [])
        self.assertFalse(self.identity().exists())
        self.assertFalse((self.cache / "example" / "build.lock").exists())
        self.assertLess(elapsed, 10.0)

    def test_authenticated_binary_pin_preserves_inherited_artifact_descriptor(self) -> None:
        artifact = self.root / "artifact-lock-descriptor"
        descriptor = os.open(artifact, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            environment = self.environment(
                None,
                extra={"FAKE_BINARY_REQUIRE_FD": str(descriptor)},
            )
            result = subprocess.run(
                [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
                cwd=self.root,
                env=environment,
                pass_fds=(descriptor,),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=15,
                check=False,
            )
        finally:
            os.close(descriptor)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("source=", result.stdout)

    def test_replaceable_nonsticky_cache_ancestor_fails_closed(self) -> None:
        shared = self.root / "replaceable-cache-parent"
        shared.mkdir()
        shared.chmod(0o777)
        cache = shared / "cache"
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra={"WIKI_GO_CMD_BIN_CACHE": os.fspath(cache)}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("cache ancestor is replaceable by another user", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_group_world_writable_environment_wrapper_fails_closed(self) -> None:
        wrapper = self.root / "unsafe-environment-wrapper"
        wrapper.write_text("#!/usr/bin/env bash\nexec \"$@\"\n", encoding="utf-8")
        wrapper.chmod(0o777)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra={"WIKI_GO_CMD_ENV_WRAPPER": os.fspath(wrapper)}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("safe root/current-user-owned executable wrapper", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_group_world_writable_command_cache_fails_closed(self) -> None:
        command_cache = self.cache / "example"
        command_cache.mkdir(parents=True)
        command_cache.chmod(0o777)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("not group/world-writable", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_symlinked_cache_root_fails_closed(self) -> None:
        real_cache = self.root / "real-cache"
        real_cache.mkdir()
        cache_alias = self.root / "cache-alias"
        cache_alias.symlink_to(real_cache, target_is_directory=True)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra={"WIKI_GO_CMD_BIN_CACHE": os.fspath(cache_alias)}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("must not cross symlinks", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_explicit_build_source_root_is_bound_but_binary_runs_from_live_root(self) -> None:
        snapshot = self.root / "snapshot"
        (snapshot / "cmd" / "example").mkdir(parents=True)
        (snapshot / "internal").mkdir()
        (snapshot / "go.mod").write_text("module example\n\ngo 1.99\n", encoding="utf-8")
        (snapshot / "go.sum").write_text("", encoding="utf-8")
        snapshot_source = snapshot / "cmd" / "example" / "main.go"
        snapshot_source.write_text("package main\nfunc main() { println(9) }\n", encoding="utf-8")
        source_contract = self.contract_for(snapshot_source.read_bytes())

        result = self.run_cached(source_contract, snapshot)
        self.assertEqual(self.build_count(), 1)
        self.assertIn(hashlib.sha256(snapshot_source.read_bytes()).hexdigest(), result.stdout)
        self.assertIn(f"runtime_pwd={self.root}", result.stdout)
        record = json.loads(self.metadata().read_text(encoding="utf-8"))
        self.assertEqual(record["build_context"]["build_source"]["root"], os.fspath(snapshot))
        self.assertRegex(record["build_context"]["build_source"]["sha256"], r"^sha256:[0-9a-f]{64}$")
        encoded_root = base64.b64encode(os.fsencode(snapshot)).decode("ascii")
        self.assertIn(f"build_source_root_base64={encoded_root}", result.stderr)

        self.run_cached(source_contract, snapshot)
        self.assertEqual(self.build_count(), 1)

    def test_non_bootstrap_fast_path_is_scoped_to_explicit_build_source_root(self) -> None:
        snapshot = self.root / "snapshot-fast"
        (snapshot / "cmd" / "example").mkdir(parents=True)
        (snapshot / "internal").mkdir()
        (snapshot / "go.mod").write_text("module example\n\ngo 1.99\n", encoding="utf-8")
        (snapshot / "go.sum").write_text("", encoding="utf-8")
        snapshot_source = snapshot / "cmd" / "example" / "main.go"
        snapshot_source.write_text("package main\nfunc main() { println(8) }\n", encoding="utf-8")

        first = self.run_cached(None, snapshot)
        self.assertEqual(self.build_count(), 1)
        self.assertIn(hashlib.sha256(snapshot_source.read_bytes()).hexdigest(), first.stdout)
        self.run_cached(None, snapshot)
        self.assertEqual(self.build_count(), 1)

        switched = self.run_cached(None)
        self.assertEqual(self.build_count(), 2)
        self.assertIn(hashlib.sha256(self.source.read_bytes()).hexdigest(), switched.stdout)

    def test_explicit_build_source_root_rejects_symlink_alias(self) -> None:
        alias = self.root / "source-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(self.contract_for(self.source.read_bytes()), alias),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("build source root must exist canonically without symlinks", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_source_mutation_during_build_fails_closed_and_releases_lock(self) -> None:
        environment = self.environment(self.contract_for(self.source.read_bytes()))
        environment["MUTATE_SOURCE_AFTER_BUILD"] = "1"
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertIn("context changed during build", result.stderr)
        self.assertFalse((self.cache / "example" / "build.lock").exists())
        self.assertFalse(self.metadata().exists())

    def test_non_bootstrap_source_mutation_during_build_fails_closed(self) -> None:
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra={"MUTATE_SOURCE_AFTER_BUILD": "1"}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertIn("context changed during build", result.stderr)
        self.assertFalse((self.cache / "example" / "build.lock").exists())
        self.assertFalse(self.identity().exists())

    def test_non_bootstrap_source_mutation_after_cache_selection_fails_before_exec(self) -> None:
        self.run_cached(None)
        self.assertEqual(self.build_count(), 1)
        call_count = self.root / "go-env-call-count"
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={
                    "FAKE_GO_ENV_CALL_COUNT_PATH": os.fspath(call_count),
                    "MUTATE_SOURCE_ON_GO_ENV_CALL": "2",
                },
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(call_count.read_text(encoding="ascii").strip(), "2")
        self.assertEqual(self.build_count(), 1)
        self.assertIn("identity changed before exec", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_bootstrap_source_mutation_after_cache_selection_fails_before_exec(self) -> None:
        source_contract = self.contract_for(self.source.read_bytes())
        self.run_cached(source_contract)
        call_count = self.root / "bootstrap-go-env-call-count"
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                source_contract,
                extra={
                    "FAKE_GO_ENV_CALL_COUNT_PATH": os.fspath(call_count),
                    "MUTATE_SOURCE_ON_GO_ENV_CALL": "2",
                },
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertEqual(call_count.read_text(encoding="ascii").strip(), "2")
        self.assertEqual(self.build_count(), 1)
        self.assertIn("refusing stale or tampered binary", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_runtime_timeout_escalates_when_cached_command_ignores_sigterm(self) -> None:
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={
                    "FAKE_BINARY_IGNORE_TERM": "1",
                    "WIKI_GO_CMD_TIMEOUT_SECONDS": "1",
                    "WIKI_GO_CMD_TIMEOUT_GRACE_SECONDS": "1",
                },
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=6,
            check=False,
        )
        elapsed = time.monotonic() - started
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn(result.returncode, (124, 137, -9), result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertLess(elapsed, 5.0, result.stderr)

    def test_build_timeout_escalates_and_releases_lock_when_builder_ignores_sigterm(self) -> None:
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={
                    "FAKE_BUILD_IGNORE_TERM": "1",
                    "WIKI_GO_CMD_BUILD_BUDGET_MS": "1000",
                    "WIKI_GO_CMD_TIMEOUT_GRACE_SECONDS": "1",
                },
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=6,
            check=False,
        )
        elapsed = time.monotonic() - started
        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn("build_finish command=./cmd/example status=fail", result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertFalse((self.cache / "example" / "build.lock").exists())
        self.assertLess(elapsed, 5.0, result.stderr)

    def test_timeout_kill_after_grace_rejects_unbounded_operator_value(self) -> None:
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={"WIKI_GO_CMD_TIMEOUT_GRACE_SECONDS": "31"},
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("must not exceed 30 seconds", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_timeout_ceiling_accepts_1800_and_rejects_1801_seconds(self) -> None:
        accepted = self.run_cached(None, extra={"WIKI_GO_CMD_TIMEOUT_SECONDS": "1800"})
        self.assertIn("source=", accepted.stdout)
        self.assertIn("budget_ms=1800000", accepted.stderr)
        self.assertNotIn("budget_ms=1805000", accepted.stderr)
        rejected = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra={"WIKI_GO_CMD_TIMEOUT_SECONDS": "1801"}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(rejected.returncode, 2, rejected.stderr)
        self.assertIn("must not exceed 1800s", rejected.stderr)

    def test_forged_authenticated_outer_timeout_marker_fails_without_recursing(self) -> None:
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={
                    "WIKI_RUN_GO_CMD_CACHED_UNDER_TIMEOUT": "v1:00000000-0000-0000-0000-000000000000:1:1",
                },
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("refusing recursive supervision", result.stderr)
        self.assertFalse(self.build_count_path.exists())
        self.assertLess(time.monotonic() - started, 2.0)

    def test_group_world_writable_timeout_executable_cannot_authenticate_supervision(self) -> None:
        timeout_path = shutil.which("timeout")
        self.assertIsNotNone(timeout_path)
        local_timeout = self.root / "tools" / "timeout"
        shutil.copy2(timeout_path, local_timeout)
        local_timeout.chmod(0o777)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("invalid authenticated outer-timeout marker", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_argument_timeout_and_budget_above_ceiling_fail_before_build(self) -> None:
        for argument in ("--max-duration=1801s", "--budget-ms=1800001"):
            with self.subTest(argument=argument):
                result = subprocess.run(
                    [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example", argument],
                    cwd=self.root,
                    env=self.environment(None),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=3,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("shard/cache/optimize", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_non_lock_mkdir_failure_fails_fast_instead_of_looping(self) -> None:
        command_cache = self.cache / "example"
        command_cache.mkdir(parents=True)
        lock = command_cache / "build.lock"
        lock.write_text("regular-file-collision\n", encoding="utf-8")
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("mkdir failed without a valid same-user lock directory", result.stderr)
        self.assertLess(elapsed, 2.0)
        self.assertEqual(lock.read_text(encoding="utf-8"), "regular-file-collision\n")
        self.assertFalse(self.build_count_path.exists())

    def test_group_world_writable_build_lock_fails_closed(self) -> None:
        lock = self.cache / "example" / "build.lock"
        lock.mkdir(parents=True)
        lock.chmod(0o777)
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("build lock directory is unsafe", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_fifo_build_lock_metadata_is_rejected_without_blocking(self) -> None:
        lock = self.cache / "example" / "build.lock"
        lock.mkdir(parents=True)
        metadata = lock / "meta"
        os.mkfifo(metadata, 0o600)
        started = time.monotonic()
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(
                None,
                extra={"WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait"},
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        elapsed = time.monotonic() - started

        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("hypothesis=lock_metadata_unsafe_or_oversized", result.stderr)
        self.assertTrue(stat.S_ISFIFO(metadata.lstat().st_mode))
        self.assertFalse(self.build_count_path.exists())
        self.assertLess(elapsed, 2.0)

    def test_waiter_reads_complete_owner_metadata_after_bounded_handshake(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        owner = subprocess.Popen(["sleep", "5"])
        metadata = lock / "meta"

        def publish_metadata() -> None:
            time.sleep(0.5)
            temporary = command_cache / ".fixture-lock-meta"
            temporary.write_text(
                "\n".join(
                    [
                        f"pid:{owner.pid}",
                        f"started_epoch:{int(time.time())}",
                        "command:fixture-owner-build",
                        "timeout_seconds:5",
                        "budget_ms:5000",
                        "stop_condition:fixture_owner_exits",
                        "lock_scope:build:./cmd/example",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            os.replace(temporary, metadata)

        publisher = threading.Thread(target=publish_metadata)
        publisher.start()
        try:
            environment = self.environment(
                None,
                extra={
                    "WIKI_GO_CMD_BUILD_LOCK_META_INIT_GRACE_MS": "1500",
                    "WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                },
            )
            started = time.monotonic()
            result = subprocess.run(
                [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
                cwd=self.root,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            elapsed = time.monotonic() - started
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn(f"pid={owner.pid}", result.stderr)
            self.assertIn("command=fixture-owner-build", result.stderr)
            self.assertNotIn("hypothesis=lock_metadata_missing", result.stderr)
            self.assertGreaterEqual(elapsed, 0.35)
            self.assertLess(elapsed, 2.5)
        finally:
            publisher.join(timeout=2)
            owner.terminate()
            owner.wait(timeout=2)

    def test_malformed_metadata_is_not_reclaimed_before_stale_budget(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        metadata = lock / "meta"
        metadata.write_text("started_epoch:1\ncommand:partial-owner\n", encoding="utf-8")
        environment = self.environment(
            None,
            extra={
                "WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                "WIKI_GO_CMD_BUILD_LOCK_STALE_SECONDS": "900",
            },
        )
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 75, result.stderr)
        self.assertIn("pid=unknown", result.stderr)
        self.assertTrue(metadata.is_file())
        self.assertFalse(self.build_count_path.exists())

    def test_critical_wait_rejects_owner_pid_mismatch(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        owner = subprocess.Popen(["sleep", "5"])
        try:
            (lock / "meta").write_text(
                "\n".join(
                    [
                        f"pid:{owner.pid}",
                        f"started_epoch:{int(time.time())}",
                        "command:fixture-owner-build",
                        "timeout_seconds:5",
                        "budget_ms:5000",
                        "stop_condition:fixture_owner_exits",
                        "lock_scope:build:./cmd/example",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            environment = self.environment(
                None,
                extra={
                    "WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "critical_dependency",
                    "WIKI_GO_CMD_BUILD_LOCK_DEPENDENCY_ID": "fixture-dependency",
                    "WIKI_GO_CMD_BUILD_LOCK_OWNER_PID": str(owner.pid + 100000),
                    "WIKI_GO_CMD_BUILD_LOCK_WAIT_TIMEOUT_MS": "1000",
                    "WIKI_GO_CMD_BUILD_LOCK_LAST_EVIDENCE": "fixture-evidence",
                    "WIKI_GO_CMD_BUILD_LOCK_REORIENTATION_COMMAND": "fixture-command",
                },
            )
            result = subprocess.run(
                [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
                cwd=self.root,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            self.assertEqual(result.returncode, 75, result.stderr)
            self.assertIn(f"owner_pid_mismatch(observed={owner.pid})", result.stderr)
            self.assertTrue(lock.is_dir())
            self.assertFalse(self.build_count_path.exists())
        finally:
            owner.terminate()
            owner.wait(timeout=2)

    def test_reused_live_pid_identity_does_not_keep_dead_owner_lock(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        owner = subprocess.Popen(["sleep", "5"])
        try:
            boot_id = pathlib.Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
            stat_line = pathlib.Path(f"/proc/{owner.pid}/stat").read_text(encoding="ascii")
            fields_after_comm = stat_line[stat_line.rfind(") ") + 2 :].split()
            actual_start_ticks = int(fields_after_comm[19])
            (lock / "meta").write_text(
                "\n".join(
                    [
                        f"pid:{owner.pid}",
                        f"owner_boot_id:{boot_id}",
                        f"owner_start_ticks:{actual_start_ticks + 1}",
                        f"started_epoch:{int(time.time())}",
                        "command:dead-owner-whose-pid-was-reused",
                        "timeout_seconds:5",
                        "budget_ms:5000",
                        "stop_condition:dead_owner",
                        "lock_scope:build:./cmd/example",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            result = self.run_cached(None)
            self.assertEqual(self.build_count(), 1)
            self.assertIn("reclaimed reused-pid build lock", result.stderr)
            self.assertIsNone(owner.poll(), "the unrelated live process must not be killed")
            self.assertFalse(lock.exists())
        finally:
            owner.terminate()
            owner.wait(timeout=2)

    # ── 2026-07-31: staleness/liberacao de lock sem depender de DELETE ────────
    # Regressao real: em mount que nega unlink/rmdir (EPERM) o lock de uma
    # sessao morta ficava orfao PARA SEMPRE, porque todo reclaim terminava em
    # "rm -f meta || return 1". Os tres cenarios abaixo cobrem lock ausente,
    # lock com detentor vivo e lock orfao de verdade.
    @staticmethod
    def _start_ticks(pid: int) -> int:
        stat_line = pathlib.Path(f"/proc/{pid}/stat").read_text(encoding="ascii")
        return int(stat_line[stat_line.rfind(") ") + 2 :].split()[19])

    @staticmethod
    def _owner_metadata(pid: int, boot_id: str, start_ticks: int, started: int) -> str:
        return "\n".join(
            [
                f"pid:{pid}",
                f"owner_boot_id:{boot_id}",
                f"owner_start_ticks:{start_ticks}",
                f"started_epoch:{started}",
                "command:fixture-owner-build",
                "timeout_seconds:5",
                "budget_ms:5000",
                "stop_condition:fixture_owner_exits",
                "lock_scope:build:./cmd/example",
                "",
            ]
        )

    @staticmethod
    def _owner_heartbeat(pid: int, boot_id: str, start_ticks: int, epoch: int) -> str:
        return "\n".join(
            [
                f"pid:{pid}",
                f"boot_id:{boot_id}",
                f"start_ticks:{start_ticks}",
                f"epoch:{epoch}",
                "",
            ]
        )

    def _run_wrapper(self, extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        # Diferente de run_cached, nao exige exit 0: estes testes julgam o
        # CONTRATO DE LOCK (adquirir/respeitar/reciclar/liberar), que se decide
        # antes da instalacao do binario. Amarra-los ao exit final acoplaria o
        # lock a cadeia de identidade/instalacao, que tem cobertura propria.
        return subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
            cwd=self.root,
            env=self.environment(None, extra=extra),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )

    def test_absent_build_lock_is_acquired_and_released_without_delete(self) -> None:
        lock = self.cache / "example" / "build.lock"
        self.assertFalse(lock.exists())
        result = self._run_wrapper()
        # build_start so e emitido depois de acquire_build_lock + metadata.
        self.assertIn("build_start command=./cmd/example", result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertNotIn("reclaimed", result.stderr)
        # A liberacao tem de deixar o caminho livre para o proximo mkdir mesmo
        # onde rmdir e negado (rename atomico para o deposito de despejados).
        self.assertFalse(lock.exists())
        self.assertNotIn("failed to release build lock", result.stderr)
        # Enquanto segurou o lock, o dono publicou prova de vida.
        released = sorted((self.cache / "example" / ".build.lock.evicted").glob("*/heartbeat"))
        if released:
            self.assertIn("pid:", released[0].read_text(encoding="utf-8"))

    def test_live_heartbeat_keeps_mutual_exclusion_even_after_stale_budget(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        owner = subprocess.Popen(["sleep", "5"])
        try:
            boot_id = pathlib.Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
            start_ticks = self._start_ticks(owner.pid)
            (lock / "meta").write_text(
                self._owner_metadata(owner.pid, boot_id, start_ticks, int(time.time())),
                encoding="utf-8",
            )
            before = lock.stat()
            # Orcamento por relogio de parede zerado de proposito: quem protege
            # o detentor vivo passa a ser a prova de vida, nao o mtime.
            for label, epoch in (
                ("heartbeat fresco", int(time.time())),
                ("heartbeat parado, dono vivo", int(time.time()) - 100000),
            ):
                (lock / "heartbeat").write_text(
                    self._owner_heartbeat(owner.pid, boot_id, start_ticks, epoch),
                    encoding="utf-8",
                )
                result = subprocess.run(
                    [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
                    cwd=self.root,
                    env=self.environment(
                        None,
                        extra={
                            "WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait",
                            "WIKI_GO_CMD_BUILD_LOCK_STALE_SECONDS": "1",
                        },
                    ),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode, 75, f"{label}: {result.stderr}")
                self.assertIn("non_critical_wait forbids passive build lock sleep", result.stderr)
                self.assertNotIn("reclaimed", result.stderr, label)
                self.assertTrue(lock.is_dir(), label)
                after = lock.stat()
                self.assertEqual((before.st_dev, before.st_ino), (after.st_dev, after.st_ino), label)
                self.assertIsNone(owner.poll(), "the live holder must not be killed")
                self.assertFalse(self.build_count_path.exists(), label)
        finally:
            owner.terminate()
            owner.wait(timeout=2)

    def test_orphaned_heartbeat_lock_is_reclaimed_without_delete(self) -> None:
        command_cache = self.cache / "example"
        lock = command_cache / "build.lock"
        lock.mkdir(parents=True)
        dead = subprocess.Popen(["true"])
        dead.wait(timeout=5)
        if pathlib.Path(f"/proc/{dead.pid}").exists():
            self.skipTest("holder pid was recycled before the fixture could use it")
        boot_id = pathlib.Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
        stalled = int(time.time()) - 100000
        (lock / "meta").write_text(
            self._owner_metadata(dead.pid, boot_id, 4242, stalled),
            encoding="utf-8",
        )
        (lock / "heartbeat").write_text(
            self._owner_heartbeat(dead.pid, boot_id, 4242, stalled),
            encoding="utf-8",
        )
        result = self._run_wrapper({"WIKI_GO_CMD_BUILD_LOCK_WAIT_CLASSIFICATION": "non_critical_wait"})
        self.assertIn("reclaimed orphaned build lock by stalled heartbeat", result.stderr)
        # Reciclou E seguiu: um despejo que nao destrava o build nao resolve nada.
        self.assertIn("build_start command=./cmd/example", result.stderr)
        self.assertEqual(self.build_count(), 1)
        self.assertFalse(lock.exists())
        # O deposito guarda tanto o lock orfao despejado quanto o nosso, ja
        # liberado: o que importa e o orfao estar la, intacto, como evidencia.
        evicted = sorted((command_cache / ".build.lock.evicted").glob("*/meta"))
        self.assertTrue(evicted, "o despejo tem de ser por rename, preservando a evidencia")
        self.assertTrue(
            any(f"pid:{dead.pid}" in path.read_text(encoding="utf-8") for path in evicted),
            f"lock orfao (pid {dead.pid}) nao foi preservado no deposito de despejados",
        )

    def test_live_generate_multiplex_and_devcmds_contracts_are_preserved(self) -> None:
        source = RUNNER_SOURCE.read_text(encoding="utf-8")
        self.assertIn("./cmd/generate | ./cmd/generate-*)", source)
        self.assertIn("go-modern build -tags devcmds -o", source)
        self.assertIn("-buildvcs=false", source)
        self.assertIn('mv -fT -- "$LOCK_METADATA_TMP" "$LOCK_META"', source)
        self.assertNotRegex(source, r"(?m)^\s*mv (?!-fT -- )")
        self.assertIn('exec python3 - "$BIN" "$CURRENT_BINARY_SHA256"', source)
        self.assertIn("flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NONBLOCK", source)
        self.assertIn('pinned_binary = f"/proc/self/fd/{descriptor}"', source)
        self.assertIn("os.set_inheritable(descriptor, True)", source)
        self.assertIn("os.execve(timeout_name, timeout_arguments, os.environ)", source)

    def test_generate_contract_rejects_forged_supervisor_timing_environment(self) -> None:
        environment = self.environment(None)
        environment.update(
            {
                "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY": "1",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                "WIKI_HEAVY_BUDGET_MS": "5000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                "WIKI_HEAVY_STOP_CONDITION": "fake generator exits",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1.5",
                "WIKI_HEAVY_TIMING_MODE": "supervisor_wall_clock_v1",
            }
        )
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/generate-example", "--root", "/tmp/example"],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("supervisor_wall_clock_without_verified_run-heavy-process-tree", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_generate_contract_rejects_real_processes_with_forged_supervisor_argv(self) -> None:
        for name in HEAVY_SUPPORT:
            shutil.copy2(RUNNER_SOURCE.with_name(name), self.root / "tools" / name)
        helper = self.root / "forge-supervisor.py"
        helper.write_text(
            """import os, subprocess, sys
supervisor, runner = sys.argv[1:]
raise SystemExit(subprocess.run(
    [supervisor, '-c', '\"$1\" ./cmd/generate-example --timings', 'forged-supervisor', runner],
    executable='/bin/bash', env=os.environ.copy(), check=False,
).returncode)
""",
            encoding="utf-8",
        )
        environment = self.environment(None)
        environment.update(
            {
                "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY": "1",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                "WIKI_HEAVY_BUDGET_MS": "5000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                "WIKI_HEAVY_STOP_CONDITION": "fake generator exits",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                "WIKI_HEAVY_TIMING_MODE": "supervisor_wall_clock_v1",
            }
        )
        heavy = os.fspath(self.root / "tools" / "run-heavy-throttled")
        supervisor = os.fspath(self.root / "tools" / "supervise-process-tree")
        runner = os.fspath(self.root / "tools" / "run-go-cmd-cached")
        result = subprocess.run(
            [
                heavy,
                "-c",
                'python3 "$1" "$2" "$3"',
                "forged-heavy",
                os.fspath(helper),
                supervisor,
                runner,
            ],
            executable="/bin/bash",
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("supervisor_wall_clock_without_verified_run-heavy-process-tree", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_generate_contract_accepts_verified_run_heavy_process_tree(self) -> None:
        for name in HEAVY_SUPPORT:
            shutil.copy2(RUNNER_SOURCE.with_name(name), self.root / "tools" / name)
        (self.root / "data" / "research").mkdir(parents=True)
        (self.root / ".agents" / "runtime").mkdir(parents=True)
        environment = self.environment(None)
        environment.update(
            {
                "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                "WIKI_HEAVY_BUDGET_MS": "5000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                "WIKI_HEAVY_STOP_CONDITION": "fixture_exits",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1.5",
                "WIKI_HEAVY_TIMING_MODE": "supervisor_wall_clock_v1",
                "WIKI_HEAVY_PROGRESS_MONITOR": "off",
                "WIKI_HEAVY_LOCK_DIR": os.fspath(self.root / "heavy-locks"),
                "WIKI_HEAVY_TIMEOUT_SECONDS": "8",
                "WIKI_HEAVY_TIMEOUT_KILL_AFTER_SECONDS": "1",
            }
        )
        result = subprocess.run(
            [
                os.fspath(self.root / "tools" / "run-heavy-throttled"),
                "run-go-cmd-cached",
                "./cmd/generate-example",
                "--root",
                "/tmp/example",
            ],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("source=", result.stdout)
        self.assertIn("timing mode=supervisor_wall_clock_v1", result.stderr)

    def test_build_lock_heartbeat_renewer_leaves_no_orphan_under_strict_supervisor(
        self,
    ) -> None:
        # Regressao 2026-09-05. O renovador de heartbeat do build lock dormia em
        # PRIMEIRO plano dentro da subshell; o `kill` de
        # stop_build_lock_heartbeat_renewer alcancava a subshell e nunca o
        # `sleep`, que ficava orfao por ate
        # WIKI_GO_CMD_BUILD_LOCK_HEARTBEAT_INTERVAL_SECONDS e era adotado pelo
        # subreaper. Sob `--fail-on-descendant-cleanup` isso devolvia 125 —
        # medido: sono de 5 s contra os 1,5 s de grace do supervisor, entao a
        # corrida NUNCA se resolvia sozinha.
        #
        # O grace vai a ZERO de proposito: assim o teste nao depende de o sono
        # ser mais curto que a janela de perdao. Ou o renovador encerra o
        # proprio sono, ou isto reprova. O intervalo de 30 s torna impossivel
        # passar por acaso.
        #
        # O comando e `./cmd/example`, NAO `./cmd/generate-example`: gerador
        # exige supervisao do run-heavy-throttled com artifact_claim, budget e
        # evidencia de timing, e sob supervise-process-tree puro morre com
        # exit 2 no contrato ANTES de tomar o build lock -- o renovador nunca
        # chegaria a existir e este teste passaria a medir nada. Foi assim que
        # a primeira versao dele nasceu cega; a prova por mutacao em
        # tools/test_run_go_cmd_cached_heartbeat_mutacao.sh e o que exige que
        # ele reprove contra a ancora com o defeito.
        for name in HEAVY_SUPPORT:
            shutil.copy2(RUNNER_SOURCE.with_name(name), self.root / "tools" / name)
        environment = self.environment(None)
        # O wrapper exige que o prazo de obsolescencia cubra ao menos SEIS
        # intervalos de heartbeat; com intervalo de 30 s o default de 120 s
        # reprova em contrato (exit 2). Os dois andam juntos aqui.
        environment["WIKI_GO_CMD_BUILD_LOCK_HEARTBEAT_INTERVAL_SECONDS"] = "30"
        environment["WIKI_GO_CMD_BUILD_LOCK_HEARTBEAT_STALE_SECONDS"] = "200"
        result = subprocess.run(
            [
                os.fspath(self.root / "tools" / "supervise-process-tree"),
                "--timeout-seconds",
                "20",
                "--kill-after-seconds",
                "2",
                "--term-grace-seconds",
                "1",
                "--kill-grace-seconds",
                "2",
                "--fail-on-descendant-cleanup",
                "--teardown-race-grace-seconds",
                "0",
                "--",
                os.fspath(self.root / "tools" / "run-go-cmd-cached"),
                "./cmd/example",
            ],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        self.assertNotIn("descendant_cleanup_after_leader_exit", result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_build_lock_heartbeat_renewer_stop_is_bounded_when_term_is_ignored(
        self,
    ) -> None:
        # Regressao 2026-09-05, achada por refutacao adversarial. Quando quem
        # invoca o wrapper entra com `trap "" TERM`, o bash instala SIG_IGN nos
        # filhos assincronos e o trap TERM da subshell do renovador nunca chega
        # a ser instalado. O `kill` de stop_build_lock_heartbeat_renewer vira
        # inocuo e o `wait` sem teto que vinha depois pendurava o wrapper
        # INTEIRO ate o relogio externo — medido rc=124. O renovador virava
        # dono do relogio de quem o criou.
        #
        # Nao ha chamador conhecido que ignore TERM, e por isso mesmo o defeito
        # nunca apareceu: e a classe que so se manifesta no dia em que alguem
        # envelopa este wrapper de um jeito novo.
        #
        # POR QUE ESTE TESTE EXTRAI AS DUAS FUNCOES EM VEZ DE RODAR O WRAPPER.
        # A primeira versao dele invocava `run-go-cmd-cached ./cmd/example` sob
        # `trap "" TERM` e passava DOS DOIS LADOS — a prova por mutacao acusou
        # "o mutante PASSOU", que e o sintoma de teste cego. Medido: no wrapper
        # inteiro o renovador nao esta vivo no instante do `stop` por este
        # caminho, entao o cenario nunca era exercitado. Ja o padrao em si
        # pendura de verdade: `( while sleep 30; ...) & kill; wait` com TERM
        # ignorado nao terminou em 12 s, contra 2 ms com TERM normal.
        #
        # Extrair as duas funcoes do ARQUIVO DE PRODUCAO (nao de uma copia
        # colada aqui) mantem o teste presa ao codigo real: reverter a correcao
        # em tools/run-go-cmd-cached reprova isto na hora.
        fonte = RUNNER_SOURCE.read_text(encoding="utf-8")
        funcoes = []
        for nome in (
            "start_build_lock_heartbeat_renewer",
            "stop_build_lock_heartbeat_renewer",
        ):
            achado = re.search(
                r"^%s\(\) \{\n.*?^\}\n" % re.escape(nome), fonte, re.S | re.M
            )
            self.assertIsNotNone(achado, f"{nome} nao encontrada em {RUNNER_SOURCE}")
            funcoes.append(achado.group(0))
        roteiro = self.root / "renovador-sob-term-ignorado.sh"
        roteiro.write_text(
            "#!/usr/bin/env bash\n"
            "BUILD_LOCK_OWNED=1\n"
            "LOCK_HEARTBEAT_RENEWER_PID=''\n"
            "LOCK_HEARTBEAT_INTERVAL_SECONDS=30\n"
            "WRAPPER_PID=$$\n"
            "BUILD_LOCK_OWNED_IDENTITY=identidade\n"
            "build_lock_dir_identity() { printf 'identidade'; }\n"
            "write_build_lock_heartbeat() { return 0; }\n"
            + "\n".join(funcoes)
            + "\nstart_build_lock_heartbeat_renewer\n"
            "stop_build_lock_heartbeat_renewer\n"
            "echo encerrou\n",
            encoding="utf-8",
        )
        roteiro.chmod(0o755)
        try:
            result = subprocess.run(
                ["/bin/bash", "-c", 'trap "" TERM; exec "$0"', os.fspath(roteiro)],
                cwd=self.root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Teto curto de proposito: sem a espera limitada, o `wait` nu
                # segura ate o relogio de quem chamou, e e isso que se quer ver
                # estourar. TimeoutExpired vira falha nomeada em vez de erro
                # cru, para o veredito dizer o que aconteceu.
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "stop_build_lock_heartbeat_renewer pendurou com TERM ignorado: "
                "o `kill` nao alcanca a subshell e a espera nao tem teto"
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("encerrou", result.stdout)

    def test_build_lock_heartbeat_interval_rejects_zero_padded_values(self) -> None:
        # Regressao 2026-09-05, achada por refutacao adversarial. O `case` que
        # valida o intervalo recusava `0` e ACEITAVA `00`, `000` e `007`:
        #
        #   - `sleep 00` volta em 2 ms, e o renovador reescreveu o heartbeat
        #     105+ vezes em 2 s, queimando CPU durante todo o build;
        #   - `007` e pior porque PARECE 7 e nao e: o teto `-gt 60` compara em
        #     base 8, entao o operador que escreve 007 nao recebe nem o erro
        #     nem o intervalo que pediu.
        #
        # Nenhum dos dois e defeito da correcao do renovador — sao anteriores a
        # ela. Mas so apareceram porque alguem foi procurar, e sem teste voltam.
        for valor in ("00", "000", "007", "0"):
            with self.subTest(valor=valor):
                environment = self.environment(None)
                environment["WIKI_GO_CMD_BUILD_LOCK_HEARTBEAT_INTERVAL_SECONDS"] = valor
                result = subprocess.run(
                    [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/example"],
                    cwd=self.root,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=60,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(
                    "WIKI_GO_CMD_BUILD_LOCK_HEARTBEAT_INTERVAL_SECONDS must be a positive integer",
                    result.stderr,
                )

    def test_generate_child_flag_capability_fails_when_flag_is_absent(self) -> None:
        environment = self.environment(None)
        environment.update(
            {
                "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY": "1",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                "WIKI_HEAVY_BUDGET_MS": "5000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                "WIKI_HEAVY_STOP_CONDITION": "fake generator exits",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                "WIKI_HEAVY_TIMING_MODE": "child_flag_v1",
            }
        )
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/generate-example"],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--timings(child_flag_v1 capability)", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_generate_child_timing_cannot_forge_run_heavy_environment(self) -> None:
        environment = self.environment(None)
        environment.update(
            {
                "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY": "1",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                "WIKI_HEAVY_BUDGET_MS": "5000",
                "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                "WIKI_HEAVY_STOP_CONDITION": "fake generator exits",
                "WIKI_HEAVY_THROUGHPUT_EXPECTED": "records_per_second=1",
                "WIKI_HEAVY_TIMING_MODE": "child_flag_v1",
            }
        )
        result = subprocess.run(
            [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/generate-example", "--timings"],
            cwd=self.root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("missing: run-heavy-throttled", result.stderr)
        self.assertFalse(self.build_count_path.exists())

    def test_generate_throughput_contract_rejects_numeric_prefix_garbage_and_zero(self) -> None:
        for throughput in ("records_per_second=1bogus", "records_per_second=0", "throughput=0.0"):
            with self.subTest(throughput=throughput):
                environment = self.environment(None)
                environment.update(
                    {
                        "WIKI_RUN_GO_CMD_CACHED_UNDER_HEAVY": "1",
                        "WIKI_HEAVY_ARTIFACT_CLAIM_PATH": "data/research/example.jsonl",
                        "WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER": "contract-test",
                        "WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED": "updated_or_stable:data/research/example.jsonl",
                        "WIKI_HEAVY_BUDGET_MS": "5000",
                        "WIKI_HEAVY_EXPECTED_DURATION_MS": "1000",
                        "WIKI_HEAVY_STOP_CONDITION": "fake generator exits",
                        "WIKI_HEAVY_THROUGHPUT_EXPECTED": throughput,
                        "WIKI_HEAVY_TIMING_MODE": "child_flag_v1",
                    }
                )
                result = subprocess.run(
                    [os.fspath(self.root / "tools" / "run-go-cmd-cached"), "./cmd/generate-example", "--timings"],
                    cwd=self.root,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("throughput_expected", result.stderr)
        self.assertFalse(self.build_count_path.exists())


if __name__ == "__main__":
    unittest.main()
