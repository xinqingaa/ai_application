#!/usr/bin/env python3
"""Locate Fireworks or install the pinned backend into a shared user path."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast


SKILL_NAME = "fireworks-tech-graph"
REQUIRED_FILES = (
    "SKILL.md",
    "scripts/fireworks.py",
    "schemas/diagram-v1.schema.json",
    "references/composition-quality-contract.md",
)
LOCK_FILE = (
    Path(__file__).resolve().parent.parent / "references" / "fireworks-source.lock.json"
)


class FireworksInstallError(RuntimeError):
    """Raised when the pinned Fireworks backend cannot be installed safely."""


@dataclass(frozen=True)
class SourceLock:
    repository: str
    commit: str
    skill_path: str


def _emit_unique(path: Path, seen: set[Path]) -> Iterable[Path]:
    resolved = path.expanduser().resolve()
    if resolved not in seen:
        seen.add(resolved)
        yield resolved


def candidate_roots(explicit: Path | None = None) -> Iterable[Path]:
    """Yield supported Fireworks locations in compatibility order."""
    seen: set[Path] = set()

    if explicit is not None:
        yield from _emit_unique(explicit, seen)

    environment_root = os.environ.get("FIREWORKS_SKILL_ROOT")
    if environment_root:
        yield from _emit_unique(Path(environment_root), seen)

    codex_root = os.environ.get("CODEX_HOME")
    if codex_root:
        yield from _emit_unique(Path(codex_root) / "skills" / SKILL_NAME, seen)

    home = Path.home()
    for path in (
        home / ".codex" / "skills" / SKILL_NAME,
        home / ".agents" / "skills" / SKILL_NAME,
        home / ".claude" / "skills" / SKILL_NAME,
        home / ".cursor" / "skills" / SKILL_NAME,
        home / ".local" / "share" / "agent-skills" / SKILL_NAME,
    ):
        yield from _emit_unique(path, seen)


def is_complete(root: Path) -> bool:
    return all((root / relative).is_file() for relative in REQUIRED_FILES)


def find_fireworks(explicit: Path | None = None) -> Path | None:
    return next((root for root in candidate_roots(explicit) if is_complete(root)), None)


def shared_install_root(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    environment_root = os.environ.get("FIREWORKS_SKILL_ROOT")
    if environment_root:
        return Path(environment_root).expanduser().resolve()
    return (Path.home() / ".local" / "share" / "agent-skills" / SKILL_NAME).resolve()


def _load_source_lock() -> SourceLock:
    try:
        loaded = cast(object, json.loads(LOCK_FILE.read_text(encoding="utf-8")))
        if not isinstance(loaded, dict):
            raise TypeError("root value must be an object")
        payload = cast(dict[str, object], loaded)
        repository = payload.get("repository")
        commit = payload.get("commit")
        skill_path = payload.get("skill_path")
        if not all(
            isinstance(value, str) for value in (repository, commit, skill_path)
        ):
            raise TypeError("repository, commit, and skill_path must be strings")
        source = SourceLock(
            repository=cast(str, repository),
            commit=cast(str, commit),
            skill_path=cast(str, skill_path),
        )
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise FireworksInstallError(
            f"Invalid Fireworks source lock: {error}"
        ) from error

    if not source.repository.startswith("https://github.com/"):
        raise FireworksInstallError(
            "Fireworks source must be an HTTPS GitHub repository"
        )
    if len(source.commit) != 40 or any(
        char not in "0123456789abcdef" for char in source.commit
    ):
        raise FireworksInstallError(
            "Fireworks source lock must contain a full commit SHA"
        )
    source_path = Path(source.skill_path)
    if source_path.is_absolute() or ".." in source_path.parts:
        raise FireworksInstallError(
            "Fireworks skill_path must stay inside the repository"
        )
    return source


def _run_git(arguments: Sequence[str], *, timeout: int = 25) -> str:
    if shutil.which("git") is None:
        raise FireworksInstallError(
            "git is required for the first Fireworks installation"
        )
    try:
        result = subprocess.run(
            ["git", *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise FireworksInstallError("Timed out while downloading Fireworks") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise FireworksInstallError(detail)
    return result.stdout.strip()


def _validate_source_tree(root: Path) -> None:
    if not is_complete(root):
        missing = [
            relative for relative in REQUIRED_FILES if not (root / relative).is_file()
        ]
        raise FireworksInstallError(
            f"Downloaded Fireworks is incomplete: {', '.join(missing)}"
        )

    for path in root.rglob("*"):
        if path.is_symlink():
            raise FireworksInstallError(
                f"Downloaded Fireworks contains a symlink: {path}"
            )
        if not path.is_dir() and not path.is_file():
            raise FireworksInstallError(
                f"Downloaded Fireworks contains an unsupported entry: {path}"
            )


def _acquire_lock(lock_dir: Path, *, timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        try:
            lock_dir.mkdir()
            return True
        except FileExistsError:
            if find_fireworks() is not None:
                return False
            if time.monotonic() >= deadline:
                raise FireworksInstallError(
                    f"Timed out waiting for another Fireworks installation: {lock_dir}"
                )
            time.sleep(0.25)


def _install_pinned(target: Path) -> None:
    source = _load_source_lock()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FireworksInstallError(
            f"Fireworks destination already exists but is incomplete: {target}"
        )

    temporary = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}-", dir=target.parent))
    try:
        repository = temporary / "repository"
        repository.mkdir()
        _ = _run_git(["-C", str(repository), "init", "--quiet"])
        _ = _run_git(
            ["-C", str(repository), "remote", "add", "origin", source.repository]
        )
        _ = _run_git(["-C", str(repository), "sparse-checkout", "init", "--cone"])
        _ = _run_git(
            ["-C", str(repository), "sparse-checkout", "set", source.skill_path]
        )
        _ = _run_git(
            [
                "-C",
                str(repository),
                "fetch",
                "--quiet",
                "--depth",
                "1",
                "origin",
                source.commit,
            ]
        )
        _ = _run_git(
            ["-C", str(repository), "checkout", "--quiet", "--detach", "FETCH_HEAD"]
        )
        actual_commit = _run_git(["-C", str(repository), "rev-parse", "HEAD"])
        if actual_commit != source.commit:
            raise FireworksInstallError(
                f"Fireworks commit mismatch: expected {source.commit}, got {actual_commit}"
            )

        downloaded = repository / source.skill_path
        _validate_source_tree(downloaded)
        staged = temporary / SKILL_NAME
        _ = shutil.copytree(downloaded, staged)
        _validate_source_tree(staged)
        _ = os.replace(staged, target)
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def ensure_fireworks(explicit: Path | None = None) -> Path:
    """Return an existing backend, installing the pinned copy when none exists."""
    existing = find_fireworks(explicit)
    if existing is not None:
        return existing

    target = shared_install_root(explicit)
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_dir = target.parent / f".{SKILL_NAME}.install.lock"
    last_error: FireworksInstallError | None = None

    for attempt in range(2):
        acquired = _acquire_lock(lock_dir)
        if not acquired:
            existing = find_fireworks(explicit)
            if existing is None:
                raise FireworksInstallError(
                    "Another installer finished without a usable Fireworks skill"
                )
            return existing

        try:
            existing = find_fireworks(explicit)
            if existing is not None:
                return existing
            _install_pinned(target)
            if not is_complete(target):
                raise FireworksInstallError(
                    "Fireworks installation did not produce a complete backend"
                )
            return target
        except FireworksInstallError as error:
            last_error = error
        finally:
            try:
                lock_dir.rmdir()
            except OSError:
                pass

        if attempt == 0:
            time.sleep(0.5)
            existing = find_fireworks(explicit)
            if existing is not None:
                return existing

    assert last_error is not None
    raise last_error


def _print_json(value: object, *, stream: TextIO = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), file=stream)


@dataclass
class CliArgs:
    fireworks_root: Path | None = None
    check_only: bool = False
    destination_only: bool = False
    json_output: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--fireworks-root", type=Path, help="explicit backend/install path"
    )
    _ = parser.add_argument(
        "--check-only", action="store_true", help="locate without installing"
    )
    _ = parser.add_argument(
        "--destination-only",
        action="store_true",
        help="print the shared install destination",
    )
    _ = parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="print machine-readable output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv, namespace=CliArgs())
    if args.destination_only:
        root = shared_install_root(args.fireworks_root)
        if args.json_output:
            _print_json({"ok": True, "destination": str(root)})
        else:
            print(root)
        return 0

    existing = find_fireworks(args.fireworks_root)
    if args.check_only:
        if existing is None:
            if args.json_output:
                _print_json({"ok": False, "fireworks": "not-installed"})
            return 1
        root = existing
        installed = False
    else:
        try:
            root = ensure_fireworks(args.fireworks_root)
        except FireworksInstallError as error:
            if args.json_output:
                _print_json({"ok": False, "error": str(error)}, stream=sys.stderr)
            else:
                print(f"Unable to install Fireworks: {error}", file=sys.stderr)
            return 2
        installed = existing is None

    if args.json_output:
        _print_json({"ok": True, "installed": installed, "root": str(root)})
    else:
        print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
