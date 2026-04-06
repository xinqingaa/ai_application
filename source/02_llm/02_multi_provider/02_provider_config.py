"""
02_provider_config.py
Provider 配置层设计：能力矩阵、环境变量映射、请求预览、可用性检查

运行方式：
    python 02_provider_config.py
"""

from __future__ import annotations

import json

from provider_utils import (
    ChatRequest,
    compare_provider_payloads,
    get_provider_status_rows,
    load_env_if_possible,
)


def print_provider_matrix() -> None:
    print("=" * 70)
    print("1. Provider 能力矩阵")
    print("=" * 70)
    rows = get_provider_status_rows()
    for row in rows:
        print(
            f"{row['provider']:9s} | type={row['type']:18s} | ready={row['ready']} "
            f"| openai={row['openai_compatible']} | stream={row['streaming']} "
            f"| structured={row['structured']} | vision={row['vision']}"
        )
        print(f"         model={row['model']}")
        print(f"         base_url={row['base_url']}")


def print_request_preview_comparison() -> None:
    request = ChatRequest(
        messages=[
            {"role": "system", "content": "你是一个严谨的技术助教，回答要分点。"},
            {"role": "user", "content": "请解释多平台统一抽象为什么重要。"},
        ],
        temperature=0.2,
        max_tokens=240,
        stop=["END"],
        metadata={"chapter": "02_multi_provider", "demo": "preview_compare"},
    )
    previews = compare_provider_payloads(request, ["openai", "claude", "gemini"])

    print("\n" + "=" * 70)
    print("2. 不同 provider 的请求预览")
    print("=" * 70)
    for provider, payload in previews.items():
        print(f"\n[{provider}]")
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_config_layer_takeaways() -> None:
    print("\n" + "=" * 70)
    print("3. 配置层应该负责什么")
    print("=" * 70)
    print("配置层应该集中描述：")
    print("1. provider 的名称、类型、默认模型、默认 base_url")
    print("2. 需要读取哪些环境变量")
    print("3. 当前平台的能力矩阵")
    print("4. 当前平台是否是 OpenAI-compatible")
    print()
    print("配置层不应该负责：")
    print("1. 业务逻辑分支")
    print("2. 页面文案拼接")
    print("3. 每个调用点重复判断 provider")


def main() -> None:
    load_env_if_possible()
    print_provider_matrix()
    print_request_preview_comparison()
    print_config_layer_takeaways()


if __name__ == "__main__":
    main()
