"""
llm_invoke_lab — SDK 直调对照（步骤 3 之前的基线观察）。

运行：
    uv run python first_chat.py
    uv run python first_chat.py --temperature 0.7
    uv run python first_chat.py --sample S3 --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from app_log import add_log_arguments, configure_from_args, console
from dotenv import load_dotenv
from openai import OpenAI

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parents[2]
SAMPLES_PATH = DEMO_DIR / "samples.json"

SYSTEM_PROMPT = (
    "你是需求评审助手。只根据用户材料分析，不要编造未出现的功能。"
)


def find_and_load_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
    else:
        load_dotenv()


def require_api_key() -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if api_key:
        return api_key
    console.error("未配置 OPENAI_API_KEY")
    console.error("请在仓库根目录复制 .env.example 为 .env 并填写 Key")
    console.error(f"cp {REPO_ROOT / '.env.example'} {REPO_ROOT / '.env'}")
    raise SystemExit(1)


def load_sample(sample_id: str) -> dict:
    samples = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
    by_id = {s["id"]: s for s in samples}
    if sample_id not in by_id:
        valid = ", ".join(sorted(by_id))
        console.error(f"未知样例 {sample_id!r}，可选：{valid}")
        raise SystemExit(1)
    return by_id[sample_id]


def build_messages(user_content: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="最小真实 Chat 调用")
    parser.add_argument(
        "--sample",
        default="S2",
        help="samples.json 中的样例 id（默认 S2 风险识别）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="模型 id（默认读取 OPENAI_MODEL 或 gpt-4o-mini）",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="采样温度（默认 0，便于对比实验）",
    )
    add_log_arguments(parser)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_from_args(args)
    find_and_load_env()
    api_key = require_api_key()

    model = (args.model or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini").strip()
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or None

    sample = load_sample(args.sample)
    messages = build_messages(sample["user_content"])

    client = OpenAI(api_key=api_key, base_url=base_url)

    console.title("First Chat", "OpenAI SDK direct-call baseline")
    console.field("sample", f"{sample['id']} ({sample['type']}) — {sample['summary']}")
    console.field("model", model)
    console.field("temperature", args.temperature)
    if base_url:
        console.field("base_url", base_url)

    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=args.temperature,
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    content = resp.choices[0].message.content or ""
    usage = resp.usage

    console.section("Response")
    console.field("model", resp.model)
    if usage:
        console.field(
            "usage",
            {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
        )
    else:
        console.field("usage", "(not provided)")
    console.field("latency_ms", round(latency_ms, 1))
    console.text("content preview", content[:300] + ("..." if len(content) > 300 else ""))


if __name__ == "__main__":
    main()
