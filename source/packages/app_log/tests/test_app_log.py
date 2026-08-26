from __future__ import annotations

import ast
import json
from io import StringIO
from pathlib import Path

from app_log import AppConsole, configure_logging, get_logger
from app_log.redaction import redact

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_redaction_hides_nested_sensitive_fields() -> None:
    value = {
        "api_key": "secret",
        "headers": {"Authorization": "Bearer secret"},
        "model": "demo",
        "total_tokens": 42,
    }

    assert redact(value) == {
        "api_key": "[REDACTED]",
        "headers": {"Authorization": "[REDACTED]"},
        "model": "demo",
        "total_tokens": 42,
    }


def test_json_logging_is_parseable_and_redacted() -> None:
    out = StringIO()
    err = StringIO()
    configure_logging(log_format="json", out=out, err=err)

    get_logger("rag_core.ingestion").info(
        "document.loaded",
        "文档加载完成",
        filename="rules.pdf",
        api_key="should-not-leak",
    )

    payload = json.loads(out.getvalue())
    assert payload["event_name"] == "document.loaded"
    assert payload["component"] == "rag_core.ingestion"
    assert payload["fields"]["filename"] == "rules.pdf"
    assert payload["fields"]["api_key"] == "[REDACTED]"
    assert err.getvalue() == ""


def test_json_warning_uses_stderr() -> None:
    out = StringIO()
    err = StringIO()
    configure_logging(log_format="json", out=out, err=err)

    get_logger("rag_core.ingestion").warning("pdf.warning", "需要核对")

    assert out.getvalue() == ""
    assert json.loads(err.getvalue())["level"] == "warning"


def test_console_without_color_has_no_ansi_sequences() -> None:
    out = StringIO()
    err = StringIO()
    target = AppConsole(out=out, err=err, color="never")

    target.success("完成")
    target.warning("需要核对")

    assert "\x1b[" not in out.getvalue()
    assert "\x1b[" not in err.getvalue()
    assert "SUCCESS" in out.getvalue()
    assert "WARNING" in err.getvalue()


def test_compact_logging_can_use_injected_streams() -> None:
    out = StringIO()
    err = StringIO()
    configure_logging(log_format="compact", color="never", out=out, err=err)

    logger = get_logger("rag_core.ingestion")
    logger.info("document.loaded", "文档加载完成")
    logger.error("document.failed", "文档加载失败")

    assert "document.loaded" in out.getvalue()
    assert "document.failed" in err.getvalue()


def test_application_runtime_does_not_call_builtin_print() -> None:
    roots = (
        REPO_ROOT / "source" / "packages",
        REPO_ROOT / "source" / "demos",
        REPO_ROOT / "source" / "apps",
    )
    violations: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}")

    assert violations == []


def test_llm_core_no_longer_owns_terminal_logging() -> None:
    old_path = REPO_ROOT / "source" / "packages" / "llm_core" / "observability"
    assert not any(old_path.glob("*.py"))
    old_import = "llm_core" + ".observability"
    for path in (REPO_ROOT / "source").rglob("*"):
        if path.suffix not in {".py", ".md"}:
            continue
        assert old_import not in path.read_text(encoding="utf-8")
