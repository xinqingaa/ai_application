#!/usr/bin/env python3
"""Locate and invoke Fireworks without installing or downloading it."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional, Sequence


REQUIRED_FILES = (
    "SKILL.md",
    "scripts/fireworks.py",
    "schemas/diagram-v1.schema.json",
    "references/composition-quality-contract.md",
)


def _candidate_roots(explicit: Optional[Path]) -> Iterable[Path]:
    seen: set[Path] = set()

    def emit(path: Path) -> Iterable[Path]:
        resolved = path.expanduser().resolve()
        if resolved not in seen:
            seen.add(resolved)
            yield resolved

    if explicit is not None:
        yield from emit(explicit)

    environment_root = os.environ.get("FIREWORKS_SKILL_ROOT")
    if environment_root:
        yield from emit(Path(environment_root))

    codex_root = os.environ.get("CODEX_HOME")
    if codex_root:
        yield from emit(Path(codex_root) / "skills" / "fireworks-tech-graph")

    yield from emit(Path.home() / ".codex" / "skills" / "fireworks-tech-graph")
    yield from emit(Path.home() / ".agents" / "skills" / "fireworks-tech-graph")


def _is_complete(root: Path) -> bool:
    return all((root / relative).is_file() for relative in REQUIRED_FILES)


def resolve_fireworks(explicit: Optional[Path]) -> Optional[Path]:
    return next((root for root in _candidate_roots(explicit) if _is_complete(root)), None)


def _version(root: Path) -> Optional[str]:
    package = root / "package.json"
    if not package.is_file():
        return None
    try:
        value = json.loads(package.read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        return None
    return str(value) if value else None


def _print_json(value: object, *, stream=sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), file=stream)


def _missing_payload() -> dict[str, object]:
    return {
        "ok": False,
        "fireworks": "not-installed",
        "required_files": list(REQUIRED_FILES),
        "network_attempted": False,
    }


def _require_root(args: argparse.Namespace) -> Optional[Path]:
    root = resolve_fireworks(args.fireworks_root)
    if root is None:
        _print_json(_missing_payload(), stream=sys.stderr)
    return root


def _run_fireworks(root: Path, arguments: Sequence[str]) -> int:
    command = [sys.executable, str(root / "scripts" / "fireworks.py"), *arguments]
    return subprocess.run(command, check=False).returncode


def command_detect(args: argparse.Namespace) -> int:
    root = resolve_fireworks(args.fireworks_root)
    if root is None:
        _print_json(_missing_payload())
        return 1
    _print_json({
        "ok": True,
        "fireworks": "installed",
        "root": str(root),
        "version": _version(root),
    })
    return 0


def _marker_fallback(svg: Path) -> tuple[bool, list[str]]:
    try:
        root = ET.parse(svg).getroot()
    except (OSError, ET.ParseError) as error:
        return False, [str(error)]

    declared = {element.get("id") for element in root.iter() if element.get("id")}
    missing: set[str] = set()
    pattern = re.compile(r"url\(#([^)]*)\)")
    for element in root.iter():
        for attribute in ("marker-start", "marker-mid", "marker-end"):
            value = element.get(attribute, "")
            match = pattern.fullmatch(value.strip())
            if match and match.group(1) not in declared:
                missing.add(match.group(1))
    return not missing, [f"missing marker: {item}" for item in sorted(missing)]


def command_check_svg(args: argparse.Namespace) -> int:
    svg = args.svg.resolve()
    root = resolve_fireworks(args.fireworks_root)
    if root is not None:
        checks = [
            "check",
            str(svg),
            "--check", "xml",
            "--check", "markers",
            "--check", "collisions",
            "--check", "geometry",
            "--check", "composition",
        ]
        return _run_fireworks(root, checks)

    if args.require_fireworks:
        _print_json(_missing_payload(), stream=sys.stderr)
        return 2

    passed, details = _marker_fallback(svg)
    _print_json({
        "ok": passed,
        "fireworks_validation": "skipped (not installed)",
        "fallback_checks": {
            "xml_and_marker_references": {"ok": passed, "details": details},
        },
        "visual_review_required": True,
    })
    return 0 if passed else 1


def command_render_ir(args: argparse.Namespace) -> int:
    root = _require_root(args)
    if root is None:
        return 2
    if _run_fireworks(root, ["validate", args.mode, str(args.input.resolve())]) != 0:
        return 1
    command = ["render", args.mode, str(args.input.resolve()), str(args.output.resolve())]
    if args.report is not None:
        command.extend(["--report", str(args.report.resolve())])
    return _run_fireworks(root, command)


def command_doctor(args: argparse.Namespace) -> int:
    root = _require_root(args)
    return 2 if root is None else _run_fireworks(root, ["doctor"])


def command_export_html(args: argparse.Namespace) -> int:
    root = _require_root(args)
    if root is None:
        return 2
    command = ["export-html", str(args.svg.resolve()), str(args.output.resolve())]
    if args.title:
        command.extend(["--title", args.title])
    return _run_fireworks(root, command)


def command_export_png(args: argparse.Namespace) -> int:
    root = _require_root(args)
    if root is None:
        return 2
    command = [
        str(root / "scripts" / "generate-diagram.sh"),
        "--type", args.type,
        "--style", str(args.style),
        "--output", str(args.svg.resolve()),
        "--width", str(args.width),
    ]
    return subprocess.run(command, check=False).returncode


def command_animate(args: argparse.Namespace) -> int:
    root = _require_root(args)
    if root is None:
        return 2
    command = ["animate", str(args.svg.resolve()), str(args.output.resolve())]
    if args.report is not None:
        command.extend(["--report", str(args.report.resolve())])
    return _run_fireworks(root, command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fireworks-root", type=Path, help="explicit Fireworks skill root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect", help="locate a complete Fireworks installation")
    detect.set_defaults(func=command_detect)

    check = subparsers.add_parser("check-svg", help="validate SVG with Fireworks when available")
    check.add_argument("svg", type=Path)
    check.add_argument("--require-fireworks", action="store_true")
    check.set_defaults(func=command_check_svg)

    render = subparsers.add_parser("render-ir", help="validate and render Fireworks Diagram IR")
    render.add_argument("mode")
    render.add_argument("input", type=Path)
    render.add_argument("output", type=Path)
    render.add_argument("--report", type=Path)
    render.set_defaults(func=command_render_ir)

    doctor = subparsers.add_parser("doctor", help="report Fireworks export capabilities")
    doctor.set_defaults(func=command_doctor)

    html = subparsers.add_parser("export-html", help="wrap SVG in offline interactive HTML")
    html.add_argument("svg", type=Path)
    html.add_argument("output", type=Path)
    html.add_argument("--title")
    html.set_defaults(func=command_export_html)

    png = subparsers.add_parser("export-png", help="export an existing SVG to PNG")
    png.add_argument("svg", type=Path)
    png.add_argument("--type", default="architecture")
    png.add_argument("--style", type=int, default=1)
    png.add_argument("--width", type=int, default=1920)
    png.set_defaults(func=command_export_png)

    animate = subparsers.add_parser("animate", help="render a supported semantic SVG to GIF")
    animate.add_argument("svg", type=Path)
    animate.add_argument("output", type=Path)
    animate.add_argument("--report", type=Path)
    animate.set_defaults(func=command_animate)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
