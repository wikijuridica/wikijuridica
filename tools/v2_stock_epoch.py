"""Dependency-light Python adapter for the canonical v2 stock epoch lock.

The byte-range domain is intentionally identical to internal/v2stockepoch and
the logical component of internal/v2ingest.  Python writers use a traditional
fcntl record lock, which Linux makes conflict with the Go OFD lock.  The lock
is fail-fast and process-reentrant so a finalizer can acquire global EX before
its shard locks while the central CAS safely verifies that the same lease is
already held.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hashlib
import os
import pathlib
import stat
import sys
import threading
from typing import Iterator


LOCK_NAMESPACE = pathlib.Path("/tmp")
LOCK_DOMAIN = b"portaljuridico:v2ingest-logical-root-lock:v1\0"


class StockEpochError(RuntimeError):
    """The shared epoch authority is unsafe or unavailable."""


class StockEpochBusy(StockEpochError):
    """Another reader/writer owns a conflicting epoch lease."""


_LEASE_MUTEX = threading.Lock()
_LEASE_ROOT: pathlib.Path | None = None
_LEASE_FD: int | None = None
_LEASE_OFFSET = 0
_LEASE_DEPTH = 0
_LEASE_OWNER_THREAD: int | None = None


def _reset_lease_state_after_fork() -> None:
    """Discard parent-only record-lock bookkeeping in the forked child."""
    global _LEASE_MUTEX, _LEASE_ROOT, _LEASE_FD, _LEASE_OFFSET
    global _LEASE_DEPTH, _LEASE_OWNER_THREAD
    inherited_fd = _LEASE_FD
    _LEASE_MUTEX = threading.Lock()
    _LEASE_ROOT, _LEASE_FD, _LEASE_OFFSET = None, None, 0
    _LEASE_DEPTH, _LEASE_OWNER_THREAD = 0, None
    if inherited_fd is not None:
        try:
            os.close(inherited_fd)
        except OSError:
            pass


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_lease_state_after_fork)


def _canonical_root(root: pathlib.Path | str) -> pathlib.Path:
    absolute = pathlib.Path(os.path.abspath(os.fspath(root)))
    try:
        canonical = absolute.resolve(strict=True)
    except OSError as error:
        raise StockEpochError(f"canonical stock root unavailable: {error}") from error
    if canonical != absolute or not canonical.is_dir():
        raise StockEpochError(
            f"canonical stock root contains a symlink or is not a directory: {absolute}")
    return canonical


def _lock_names() -> tuple[str, str]:
    name = f".portaljuridico-v2ingest-logical-roots-v1-{os.geteuid()}.lock"
    return name, name + ".anchor"


def _lock_offset(root: pathlib.Path) -> int:
    digest = hashlib.sha256(LOCK_DOMAIN + os.fsencode(root)).digest()
    return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)


def _validate_lock_info(name: str, info: os.stat_result) -> None:
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or
            stat.S_IMODE(info.st_mode) != 0o600):
        raise StockEpochError(
            f"stock epoch lock {name} must be regular, euid-owned mode 0600")


def _named_info(directory_fd: int, name: str) -> os.stat_result | None:
    try:
        info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    _validate_lock_info(name, info)
    return info


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _host_root_owner_uids() -> frozenset:
    """UIDs aceitos como "dono root do host" para o namespace de lock.

    Em host normal, apenas root (0). Sob user namespace com root NÃO mapeado
    (ex.: sandbox Cowork), todo arquivo do host-root aparece como o uid de
    overflow 65534 ("nobody") e é imutável para o usuário do namespace; nesse
    regime — detectado por /proc/self/uid_map sem linha mapeando o uid 0 —
    65534 carrega a mesma confiança que root. Em host sem userns, 65534
    continua reprovado como sempre. Mesma correção do trust-check do
    pre-commit (2026-07-29): falso-positivo media a promoção CAS inteira no
    sandbox ("/tmp must be a root-owned mode 01777 directory" com /tmp
    íntegro, apenas visto através do userns).
    """
    try:
        with open("/proc/self/uid_map", "rb") as handle:
            payload = handle.read(4096)
    except OSError:
        return frozenset({0})
    for line in payload.decode("ascii", errors="replace").splitlines():
        fields = line.split()
        if fields and fields[0] == "0":
            return frozenset({0})
    return frozenset({0, 65534})


_HOST_ROOT_UIDS = _host_root_owner_uids()


def _acquire(root: pathlib.Path) -> tuple[int, int]:
    namespace_before = os.lstat(LOCK_NAMESPACE)
    if (not stat.S_ISDIR(namespace_before.st_mode) or
            namespace_before.st_uid not in _HOST_ROOT_UIDS or
            stat.S_IMODE(namespace_before.st_mode) != 0o1777):
        raise StockEpochError("/tmp must be a root-owned mode 01777 directory")
    directory_fd = os.open(
        LOCK_NAMESPACE,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    try:
        namespace_open = os.fstat(directory_fd)
        if not _same_file(namespace_before, namespace_open):
            raise StockEpochError("stock epoch namespace identity changed")
        name, anchor = _lock_names()
        named = _named_info(directory_fd, name)
        anchored = _named_info(directory_fd, anchor)
        if anchored is not None and named is None:
            raise StockEpochError("stock epoch lock disappeared while anchor remains")
        if named is not None and anchored is None and named.st_nlink != 1:
            raise StockEpochError("unanchored stock epoch lock has unexpected links")
        if (named is not None and anchored is not None and
                (not _same_file(named, anchored) or
                 named.st_nlink != 2 or anchored.st_nlink != 2)):
            raise StockEpochError("stock epoch lock diverges from anchor")

        fd = os.open(
            name,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        try:
            opened = os.fstat(fd)
            _validate_lock_info(name, opened)
            offset = _lock_offset(root)
            try:
                fcntl.lockf(
                    fd, fcntl.LOCK_EX | fcntl.LOCK_NB, 1, offset, os.SEEK_SET)
            except OSError as error:
                if error.errno in {errno.EACCES, errno.EAGAIN}:
                    raise StockEpochBusy(
                        f"canonical stock epoch busy for {root}") from error
                raise
            try:
                if anchored is None:
                    try:
                        os.link(
                            name, anchor,
                            src_dir_fd=directory_fd,
                            dst_dir_fd=directory_fd,
                            follow_symlinks=False,
                        )
                    except FileExistsError:
                        pass
                named = _named_info(directory_fd, name)
                anchored = _named_info(directory_fd, anchor)
                opened = os.fstat(fd)
                if (named is None or anchored is None or opened.st_nlink != 2 or
                        named.st_nlink != 2 or anchored.st_nlink != 2 or
                        not _same_file(opened, named) or
                        not _same_file(opened, anchored)):
                    raise StockEpochError(
                        "stock epoch descriptor/path/anchor identity mismatch")
                namespace_after = os.lstat(LOCK_NAMESPACE)
                if not _same_file(namespace_open, namespace_after):
                    raise StockEpochError("stock epoch namespace changed after lock")
                return fd, offset
            except Exception:
                fcntl.lockf(fd, fcntl.LOCK_UN, 1, offset, os.SEEK_SET)
                raise
        except Exception:
            os.close(fd)
            raise
    finally:
        os.close(directory_fd)


@contextlib.contextmanager
def canonical_stock_write_lease(
    root: pathlib.Path | str,
) -> Iterator[None]:
    """Hold canonical EX from the first CAS read through the final fsync."""
    global _LEASE_ROOT, _LEASE_FD, _LEASE_OFFSET, _LEASE_DEPTH
    global _LEASE_OWNER_THREAD
    canonical = _canonical_root(root)
    owner_thread = threading.get_ident()
    with _LEASE_MUTEX:
        if _LEASE_DEPTH:
            if _LEASE_OWNER_THREAD != owner_thread:
                raise StockEpochBusy(
                    "canonical stock epoch is already held by another thread")
            if _LEASE_ROOT != canonical or _LEASE_FD is None:
                raise StockEpochError("nested stock epoch lease changed root")
            _LEASE_DEPTH += 1
        else:
            _LEASE_FD, _LEASE_OFFSET = _acquire(canonical)
            _LEASE_ROOT = canonical
            _LEASE_DEPTH = 1
            _LEASE_OWNER_THREAD = owner_thread
    try:
        yield
    finally:
        with _LEASE_MUTEX:
            if (_LEASE_OWNER_THREAD != owner_thread or _LEASE_DEPTH <= 0 or
                    _LEASE_ROOT != canonical or _LEASE_FD is None):
                raise StockEpochError(
                    "stock epoch lease ownership changed before release")
            _LEASE_DEPTH -= 1
            if _LEASE_DEPTH == 0:
                fd, offset = _LEASE_FD, _LEASE_OFFSET
                _LEASE_ROOT, _LEASE_FD, _LEASE_OFFSET = None, None, 0
                _LEASE_OWNER_THREAD = None
                try:
                    fcntl.lockf(fd, fcntl.LOCK_UN, 1, offset, os.SEEK_SET)
                finally:
                    os.close(fd)


def canonical_stock_root_for_target(
    target: pathlib.Path | str,
) -> pathlib.Path | None:
    """Return a repo root only for a path in the canonical stock domain."""
    absolute = pathlib.Path(os.path.abspath(os.fspath(target)))
    for parent in (absolute.parent, *absolute.parents):
        if not (parent / "go.mod").is_file():
            continue
        try:
            relative = absolute.relative_to(parent).as_posix()
        except ValueError:
            return None
        if (relative.startswith("data/editorial/v2_pages/") or
                relative.startswith("data/editorial/portfolio_v2/") or
                relative.startswith("data/source-registry/") or
                relative in {
                    "data/editorial/authorial_mass_drafts.jsonl",
                    "data/editorial/authorial_mass_content_expansion.jsonl",
                    "data/editorial/authorial_mass_content_expansion_section_chunks.jsonl",
                    "data/editorial/stock_manifest.json",
                }):
            return _canonical_root(parent)
        # Um go.mod aninhado/acidental não tem autoridade para desativar a
        # lease do repositório exterior. Continue até encontrar a raiz cujo
        # caminho relativo pertence de fato ao domínio canônico.
        continue
    return None


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args(argv)
    try:
        with canonical_stock_write_lease(args.root):
            print("v2-stock-epoch-python: write-lease=held publication=false")
    except StockEpochBusy as error:
        print(f"v2-stock-epoch-python: busy: {error}", file=sys.stderr)
        return 75
    except StockEpochError as error:
        print(f"v2-stock-epoch-python: unsafe: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
