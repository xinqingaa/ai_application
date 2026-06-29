"""
02_provider_switching — 02_llm/01 切换 config_ref 对比 demo。

运行：
    python provider_switching.py
    python provider_switching.py --verbose
    python provider_switching.py --configs chat.dev_chat,chat.structured_chat
"""

from __future__ import annotations

import argparse

from llm_core import LLMClient
from llm_core.errors import LLMError
from llm_core.observability import demo_log

from _shared import (
    find_and_load_env,
    load_sample,
    log_chat_result,
    log_experiment_header,
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
        help="输出完整 messages / 参数 / 响应",
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
    require_api_key(demo_log)

    sample = load_sample(args.sample, demo_log)
    messages = build_messages(sample["user_content"])
    config_refs = [c.strip() for c in args.configs.split(",") if c.strip()]

    client = LLMClient.from_default_config()

    log_experiment_header(
        demo_log,
        sample=sample,
        configs=", ".join(config_refs),
        temperature=args.temperature,
    )

    chat_kwargs: dict = {}
    if args.temperature is not None:
        chat_kwargs["temperature"] = args.temperature

    for config_ref in config_refs:
        try:
            response = client.chat(messages, config_ref, debug=False, **chat_kwargs)
            config = client.get_config(config_ref)
            merged = {**config.default_params, **chat_kwargs, "model": config.model}
            log_chat_result(
                demo_log,
                config_ref,
                response,
                verbose=args.verbose,
                messages=messages if args.verbose else None,
                params=merged if args.verbose else None,
            )
        except LLMError as exc:
            log_chat_result(demo_log, config_ref, exc)

    demo_log.hint(
        "固定 sample，只换 config_ref 或 temperature，在笔记中记录差异。"
    )


if __name__ == "__main__":
    main()
