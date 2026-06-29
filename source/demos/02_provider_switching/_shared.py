"""Shared helpers for 02_provider_switching demos."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from llm_core.config import LLMResponse
from llm_core.errors import LLMError

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
SAMPLES_PATH = DEMO_DIR.parent / "02_first_chat" / "samples.json"


def find_and_load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def require_api_key() -> None:
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return
    print("错误：未配置 OPENAI_API_KEY。", file=sys.stderr)
    print(f"请在仓库根目录复制 .env.example 为 .env 并填写 Key：", file=sys.stderr)
    print(f"  cp {REPO_ROOT / '.env.example'} {REPO_ROOT / '.env'}", file=sys.stderr)
    sys.exit(1)


def load_sample(sample_id: str) -> dict:
    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in samples}
    if sample_id not in by_id:
        valid = ", ".join(sorted(by_id))
        print(f"错误：未知样例 {sample_id!r}，可选：{valid}", file=sys.stderr)
        sys.exit(1)
    return by_id[sample_id]


def load_evidence_block(path: Path) -> str:
    if not path.is_file():
        return "（无检索证据，仅基于 Requirement 分析。）"
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("evidence_block", "")).strip() or "（Evidence 为空。）"


def print_summary_row(
    label: str,
    response: LLMResponse,
    preview_len: int = 120,
) -> None:
    tokens = response.usage.total_tokens if response.usage else "—"
    preview = response.content[:preview_len].replace("\n", " ")
    if len(response.content) > preview_len:
        preview += "..."
    print(
        f"| {label} | {response.model} | "
        f"{round(response.latency_ms, 1)} | {tokens} | {preview} |"
    )


def print_error_row(label: str, message: str, preview_len: int = 80) -> None:
    short = message.replace("\n", " ")
    if len(short) > preview_len:
        short = short[:preview_len] + "..."
    print(f"| {label} | ERROR | — | — | {short} |")


def print_results_table(
    results: list[tuple[str, LLMResponse | LLMError]],
    header_label: str = "label",
) -> None:
    print("-" * 60)
    print(f"| {header_label} | model | latency_ms | total_tokens | content_preview |")
    print("| --- | --- | --- | --- | --- |")
    for label, item in results:
        if isinstance(item, LLMError):
            print_error_row(label, str(item))
        else:
            print_summary_row(label, item)
    print("-" * 60)
