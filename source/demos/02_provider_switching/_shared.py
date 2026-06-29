"""Shared helpers for 02_provider_switching demos."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from llm_core.config import LLMResponse
from llm_core.errors import LLMError
from llm_core.observability import (
    DemoLog,
    demo_log,
    render_experiment_messages_once,
    render_structured_mode_verbose,
)
from llm_core.schemas.review import ReviewRisk
from llm_core.structured import StructuredLLMResponse

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
SAMPLES_PATH = DEMO_DIR.parent / "02_first_chat" / "samples.json"


def find_and_load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def require_api_key(log: DemoLog = demo_log) -> None:
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return
    log.error("error", "未配置 OPENAI_API_KEY。")
    log.error("error", f"请在仓库根目录复制 .env.example 为 .env 并填写 Key：")
    log.error("error", f"  cp {REPO_ROOT / '.env.example'} {REPO_ROOT / '.env'}")
    sys.exit(1)


def load_sample(sample_id: str, log: DemoLog = demo_log) -> dict:
    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in samples}
    if sample_id not in by_id:
        valid = ", ".join(sorted(by_id))
        log.error("error", f"未知样例 {sample_id!r}，可选：{valid}")
        sys.exit(1)
    return by_id[sample_id]


def load_evidence_block(path: Path) -> str:
    if not path.is_file():
        return "（无检索证据，仅基于 Requirement 分析。）"
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("evidence_block", "")).strip() or "（Evidence 为空。）"


def log_experiment_header(
    log: DemoLog,
    *,
    sample: dict,
    temperature: Optional[float] = None,
    evidence_file: Optional[Path] = None,
    prompt: Optional[str] = None,
    versions: Optional[str] = None,
    configs: Optional[str] = None,
    config_ref: Optional[str] = None,
    model: Optional[str] = None,
    modes: Optional[str] = None,
) -> None:
    log.section("experiment")
    log.field("sample", f"{sample['id']} ({sample['type']}) — {sample['summary']}", indent=1)
    if prompt:
        log.field("prompt", prompt, indent=1)
    if versions:
        log.field("versions", versions, indent=1)
    if configs:
        log.field("configs", configs, indent=1)
    if config_ref:
        suffix = f" (model={model})" if model else ""
        log.field("config_ref", f"{config_ref}{suffix}", indent=1)
    if modes:
        log.field("modes", modes, indent=1)
    if temperature is not None:
        log.field("temperature", temperature, indent=1)
    if evidence_file is not None:
        log.field("evidence", evidence_file.name, indent=1)
    log.blank()


def _shorten(value: str, *, limit: int = 120) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def log_review_risk(log: DemoLog, index: int, risk: ReviewRisk, *, indent: int = 2) -> None:
    """Print one parsed ReviewRisk with all fields and shortened long values."""
    log.field(f"risk {index}", None, indent=indent)
    log.field("title", _shorten(risk.title, limit=80), indent=indent + 1)
    log.field("category", risk.category.value, indent=indent + 1)
    log.field("level", risk.level.value, indent=indent + 1)
    log.field("rationale", _shorten(risk.rationale, limit=120), indent=indent + 1)
    if risk.citations:
        log.field("citations", len(risk.citations), indent=indent + 1)
        for j, cite in enumerate(risk.citations, 1):
            excerpt = cite.excerpt or ""
            log.field(f"citation {j}", None, indent=indent + 2)
            log.field("source_id", _shorten(cite.source_id, limit=60), indent=indent + 3)
            log.field("excerpt", _shorten(excerpt, limit=100), indent=indent + 3)
    else:
        log.field("citations", 0, indent=indent + 1)


def log_chat_result(
    log: DemoLog,
    label: str,
    item: LLMResponse | LLMError,
    *,
    verbose: bool = False,
    messages: Optional[list[dict[str, str]]] = None,
    params: Optional[dict[str, Any]] = None,
) -> None:
    log.section(label)
    if isinstance(item, LLMError):
        log.field("status", "ERROR", indent=1)
        log.text("error", str(item), indent=1)
        return

    tokens = item.usage.total_tokens if item.usage else "—"
    log.field("status", "ok", indent=1)
    log.field("model", item.model, indent=1)
    log.field("latency_ms", round(item.latency_ms, 1), indent=1)
    log.field("tokens", tokens, indent=1)
    if verbose and messages is not None and params is not None:
        from llm_core.observability import render_call_log

        render_call_log(log, messages, params, item)
    else:
        log.text("content", item.content, indent=1)
    log.blank()


def _parse_summary(result: StructuredLLMResponse) -> str:
    parse = result.parse
    if parse.ok:
        return f"ok, {parse.risk_count} risks"
    return f"fail({parse.error_stage}): {parse.message or '—'}"


def log_structured_mode_result(
    log: DemoLog,
    mode: str,
    *,
    structured_mode: str,
    result: Optional[StructuredLLMResponse] = None,
    error: Optional[LLMError] = None,
    verbose: bool = False,
    request_params: Optional[dict[str, Any]] = None,
) -> None:
    log.section(mode)
    log.field("structured_mode", structured_mode, indent=1)

    if error is not None:
        log.field("status", "API_ERROR", indent=1)
        if verbose and request_params is not None:
            log.text(
                "request_params",
                json.dumps(request_params, ensure_ascii=False, indent=2),
                indent=1,
            )
            log.text("response_error", str(error), indent=1)
        else:
            log.text("error", str(error), indent=1)
        log.blank()
        return

    assert result is not None
    parse = result.parse
    llm = result.llm
    status = "ok" if parse.ok else f"parse_fail({parse.error_stage})"
    tokens = llm.usage.total_tokens if llm.usage else "—"

    log.field("status", status, indent=1)
    log.field("model", llm.model, indent=1)
    log.field("latency_ms", round(llm.latency_ms, 1), indent=1)
    log.field("tokens", tokens, indent=1)

    if verbose:
        params = request_params if request_params is not None else result.request_params
        render_structured_mode_verbose(
            log,
            request_params=params,
            response=llm,
            parse_result=_parse_summary(result),
        )
    elif parse.ok and parse.risks:
        log.field("parse", _parse_summary(result), indent=1)
        for i, risk in enumerate(parse.risks, 1):
            log_review_risk(log, i, risk)
    elif not parse.ok:
        log.field("parse", _parse_summary(result), indent=1)
        if parse.message:
            log.text("parse_error", parse.message, indent=1)

    log.blank()
