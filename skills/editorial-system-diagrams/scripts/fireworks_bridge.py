#!/usr/bin/env python3
"""Locate, bootstrap, and invoke the pinned Fireworks backend."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO, cast

SCRIPT_DIR = Path(__file__).resolve().parent
ENSURE_SCRIPT = SCRIPT_DIR / "ensure_fireworks.py"
REQUIRED_FILES = (
    "SKILL.md",
    "scripts/fireworks.py",
    "schemas/diagram-v1.schema.json",
    "references/composition-quality-contract.md",
)


def _json_object(text: str) -> dict[str, object] | None:
    try:
        loaded = cast(object, json.loads(text))
    except ValueError:
        return None
    return cast(dict[str, object], loaded) if isinstance(loaded, dict) else None


def _version(root: Path) -> str | None:
    package = root / "package.json"
    if not package.is_file():
        return None
    try:
        payload = _json_object(package.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if payload is None:
        return None
    value = payload.get("version")
    return value if isinstance(value, str) and value else None


def _print_json(value: object, *, stream: TextIO = sys.stdout) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), file=stream)


def _missing_payload() -> dict[str, object]:
    return {
        "ok": False,
        "fireworks": "not-installed",
        "required_files": list(REQUIRED_FILES),
        "installation_attempted": False,
    }


def _resolve_backend(explicit: Path | None, *, check_only: bool) -> Path | None:
    command = [sys.executable, str(ENSURE_SCRIPT), "--json"]
    if explicit is not None:
        command.extend(["--fireworks-root", str(explicit)])
    if check_only:
        command.append("--check-only")

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        if not check_only:
            detail = result.stderr.strip() or result.stdout.strip()
            if detail:
                print(detail, file=sys.stderr)
        return None

    payload = _json_object(result.stdout)
    root_value = payload.get("root") if payload is not None else None
    if not isinstance(root_value, str):
        if not check_only:
            _print_json(
                {
                    "ok": False,
                    "fireworks": "install-failed",
                    "installation_attempted": True,
                    "error": "Fireworks bootstrapper returned an invalid root",
                },
                stream=sys.stderr,
            )
        return None
    return Path(root_value)


def _require_root(args: "BridgeArgs") -> Path | None:
    return _resolve_backend(args.fireworks_root, check_only=False)


def _run_fireworks(root: Path, arguments: Sequence[str]) -> int:
    command = [sys.executable, str(root / "scripts" / "fireworks.py"), *arguments]
    return subprocess.run(command, check=False).returncode


def command_detect(args: "BridgeArgs") -> int:
    root = _resolve_backend(args.fireworks_root, check_only=True)
    if root is None:
        _print_json(_missing_payload())
        return 1
    _print_json(
        {
            "ok": True,
            "fireworks": "installed",
            "root": str(root),
            "version": _version(root),
        }
    )
    return 0


def command_ensure(args: "BridgeArgs") -> int:
    root = _require_root(args)
    if root is None:
        return 2
    _print_json(
        {
            "ok": True,
            "fireworks": "installed",
            "root": str(root),
            "version": _version(root),
        }
    )
    return 0


def _marker_fallback(svg: Path) -> tuple[bool, list[str]]:
    try:
        root = ET.parse(svg).getroot()
    except (OSError, ET.ParseError) as error:
        return False, [str(error)]

    declared = {
        identifier
        for element in root.iter()
        if (identifier := element.get("id")) is not None
    }
    missing: set[str] = set()
    pattern = re.compile(r"url\(#([^)]*)\)")
    for element in root.iter():
        for attribute in ("marker-start", "marker-mid", "marker-end"):
            value = element.get(attribute, "")
            match = pattern.fullmatch(value.strip())
            if match and match.group(1) not in declared:
                missing.add(match.group(1))
    return not missing, [f"missing marker: {item}" for item in sorted(missing)]


def command_check_svg(args: "BridgeArgs") -> int:
    assert args.svg is not None
    svg = args.svg.resolve()
    root = _require_root(args)
    if root is not None:
        checks = [
            "check",
            str(svg),
            "--check",
            "xml",
            "--check",
            "markers",
            "--check",
            "collisions",
            "--check",
            "geometry",
            "--check",
            "composition",
        ]
        return _run_fireworks(root, checks)

    if args.require_fireworks or not args.allow_basic_fallback:
        return 2

    passed, details = _marker_fallback(svg)
    _print_json(
        {
            "ok": passed,
            "fireworks_validation": "skipped (not installed)",
            "fallback_checks": {
                "xml_and_marker_references": {"ok": passed, "details": details},
            },
            "visual_review_required": True,
        }
    )
    return 0 if passed else 1


def command_render_ir(args: "BridgeArgs") -> int:
    assert args.mode is not None
    assert args.input_path is not None
    assert args.output is not None
    root = _require_root(args)
    if root is None:
        return 2
    if (
        _run_fireworks(root, ["validate", args.mode, str(args.input_path.resolve())])
        != 0
    ):
        return 1
    command = [
        "render",
        args.mode,
        str(args.input_path.resolve()),
        str(args.output.resolve()),
    ]
    if args.report is not None:
        command.extend(["--report", str(args.report.resolve())])
    return _run_fireworks(root, command)


def command_doctor(args: "BridgeArgs") -> int:
    root = _require_root(args)
    return 2 if root is None else _run_fireworks(root, ["doctor"])


def command_export_html(args: "BridgeArgs") -> int:
    assert args.svg is not None
    assert args.output is not None
    root = _require_root(args)
    if root is None:
        return 2
    command = ["export-html", str(args.svg.resolve()), str(args.output.resolve())]
    if args.title:
        command.extend(["--title", args.title])
    return _run_fireworks(root, command)


def command_export_png(args: "BridgeArgs") -> int:
    assert args.svg is not None
    root = _require_root(args)
    if root is None:
        return 2
    command = [
        str(root / "scripts" / "generate-diagram.sh"),
        "--type",
        args.diagram_type,
        "--style",
        str(args.style),
        "--output",
        str(args.svg.resolve()),
        "--width",
        str(args.width),
    ]
    return subprocess.run(command, check=False).returncode


def command_animate(args: "BridgeArgs") -> int:
    assert args.svg is not None
    assert args.output is not None
    root = _require_root(args)
    if root is None:
        return 2
    command = ["animate", str(args.svg.resolve()), str(args.output.resolve())]
    if args.report is not None:
        command.extend(["--report", str(args.report.resolve())])
    return _run_fireworks(root, command)


Command = Callable[["BridgeArgs"], int]


@dataclass
class BridgeArgs:
    fireworks_root: Path | None = None
    command: str | None = None
    svg: Path | None = None
    mode: str | None = None
    input_path: Path | None = None
    output: Path | None = None
    report: Path | None = None
    title: str | None = None
    diagram_type: str = "architecture"
    style: int = 1
    width: int = 1920
    require_fireworks: bool = False
    allow_basic_fallback: bool = False
    func: Command | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--fireworks-root", type=Path, help="explicit Fireworks skill root"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser(
        "detect", help="locate a complete Fireworks installation"
    )
    _ = detect.set_defaults(func=command_detect)

    ensure = subparsers.add_parser(
        "ensure", help="locate or install the pinned Fireworks backend"
    )
    _ = ensure.set_defaults(func=command_ensure)

    check = subparsers.add_parser(
        "check-svg", help="validate SVG with Fireworks when available"
    )
    _ = check.add_argument("svg", type=Path)
    _ = check.add_argument("--require-fireworks", action="store_true")
    _ = check.add_argument("--allow-basic-fallback", action="store_true")
    _ = check.set_defaults(func=command_check_svg)

    render = subparsers.add_parser(
        "render-ir", help="validate and render Fireworks Diagram IR"
    )
    _ = render.add_argument("mode")
    _ = render.add_argument("input_path", metavar="input", type=Path)
    _ = render.add_argument("output", type=Path)
    _ = render.add_argument("--report", type=Path)
    _ = render.set_defaults(func=command_render_ir)

    doctor = subparsers.add_parser(
        "doctor", help="report Fireworks export capabilities"
    )
    _ = doctor.set_defaults(func=command_doctor)

    html = subparsers.add_parser(
        "export-html", help="wrap SVG in offline interactive HTML"
    )
    _ = html.add_argument("svg", type=Path)
    _ = html.add_argument("output", type=Path)
    _ = html.add_argument("--title")
    _ = html.set_defaults(func=command_export_html)

    png = subparsers.add_parser("export-png", help="export an existing SVG to PNG")
    _ = png.add_argument("svg", type=Path)
    _ = png.add_argument("--type", dest="diagram_type", default="architecture")
    _ = png.add_argument("--style", type=int, default=1)
    _ = png.add_argument("--width", type=int, default=1920)
    _ = png.set_defaults(func=command_export_png)

    animate = subparsers.add_parser(
        "animate", help="render a supported semantic SVG to GIF"
    )
    _ = animate.add_argument("svg", type=Path)
    _ = animate.add_argument("output", type=Path)
    _ = animate.add_argument("--report", type=Path)
    _ = animate.set_defaults(func=command_animate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv, namespace=BridgeArgs())
    if args.func is None:
        raise RuntimeError("No Fireworks bridge command selected")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
