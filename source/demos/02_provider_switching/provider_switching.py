"""
02_provider_switching — 02_llm/01 切换 config_ref 对比 demo。

运行：
    python provider_switching.py
    python provider_switching.py --verbose
    python provider_switching.py --configs chat.dev_chat,chat.structured_chat
"""

from __future__ import annotations

import argparse
import sys

from llm_core import LLMClient
from llm_core.config import LLMResponse
from llm_core.errors import LLMError
from llm_core.observability import format_call_log

from _shared import (
    find_and_load_env,
    load_sample,
    print_results_table,
    require_api_key,
)

SYSTEM_PROMPT = (
    "你是需求评审助手。只根据用户材料分析，不要编造未出现的功能。"
)

DEFAULT_CONFIGS = ["chat.dev_chat", "chat.structured_chat"]


def build_messages(user_content: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="02_llm/01 Provider / config_ref 对比")
    parser.add_argument("--sample", default="S2", help="samples.json 中的样例 id")
    parser.add_argument(
        "--configs",
        default=",".join(DEFAULT_CONFIGS),
        help="逗号分隔的 config_ref，如 chat.dev_chat,chat.structured_chat",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="表后打印完整 messages / 参数 / 响应",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="覆盖所有 config 的 temperature（可选）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    find_and_load_env()
    require_api_key()

    sample = load_sample(args.sample)
    messages = build_messages(sample["user_content"])
    config_refs = [c.strip() for c in args.configs.split(",") if c.strip()]

    client = LLMClient.from_default_config()

    print(f"sample: {sample['id']} ({sample['type']}) — {sample['summary']}")
    print(f"configs: {', '.join(config_refs)}")
    if args.temperature is not None:
        print(f"temperature override: {args.temperature}")

    chat_kwargs: dict = {}
    if args.temperature is not None:
        chat_kwargs["temperature"] = args.temperature

    results: list[tuple[str, LLMResponse | LLMError]] = []
    for config_ref in config_refs:
        try:
            response = client.chat(messages, config_ref, debug=False, **chat_kwargs)
        except LLMError as exc:
            results.append((config_ref, exc))
            continue
        results.append((config_ref, response))

    print_results_table(results, header_label="config_ref")

    if args.verbose:
        print("\n【详细日志】")
        for config_ref, item in results:
            if isinstance(item, LLMError):
                print(f"\n>>> verbose: {config_ref} (ERROR)\n{item}")
                continue
            config = client.get_config(config_ref)
            merged = {**config.default_params, **chat_kwargs, "model": config.model}
            print(f"\n>>> verbose: {config_ref}")
            print(format_call_log(messages, merged, item))

    print("对比实验建议：固定 sample=S2，只换 config_ref 或 temperature，在笔记中记录 notes。")


if __name__ == "__main__":
    main()
