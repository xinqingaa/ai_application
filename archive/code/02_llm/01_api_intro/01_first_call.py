"""
01_first_call.py
第一条 LLM 请求：从配置、请求体、响应结构到错误排查

运行方式：
    python 01_first_call.py

依赖：
    pip install openai python-dotenv
"""

from __future__ import annotations

import json

from llm_utils import (
    ProviderConfig,
    call_openai_compatible_chat,
    load_env_if_possible,
    load_provider_config,
    mock_chat_response,
)


def print_config_summary(config: ProviderConfig) -> None:
    print("=" * 70)
    print("1. 当前运行配置")
    print("=" * 70)
    print(f"provider: {config.provider}")
    print(f"base_url: {config.base_url or '(SDK 默认)'}")
    print(f"model: {config.model}")
    print(f"api_key: {'已配置' if config.api_key else '未配置'}")
    print()
    print("关键理解：")
    print("1. provider 决定你在用哪个平台")
    print("2. base_url 决定请求发往哪个兼容端点")
    print("3. model 决定具体调用哪个模型")


def build_demo_messages() -> list[dict[str, str]]:
    # 这里故意保留一个最小但完整的 messages 示例：
    # system 负责定义助手角色，user 负责提出本轮问题。
    # 先建立这个基本结构感，比一上来就讲复杂封装更重要。
    return [
        {"role": "system", "content": "你是一个有帮助的 AI 助手，回答要简洁。"},
        {"role": "user", "content": "你好，请用 3 句话介绍一下你自己，并说明你能帮助我做什么。"},
    ]


def print_request_anatomy(config: ProviderConfig, messages: list[dict[str, str]]) -> None:
    print("\n" + "=" * 70)
    print("2. 请求体结构拆解")
    print("=" * 70)
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 256,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()
    print("关键理解：")
    print("- model: 这次调用使用哪个模型")
    print("- messages: 本次请求的全部上下文")
    print("- temperature: 输出发散程度")
    print("- max_tokens: 输出长度上限")


def print_response_anatomy() -> None:
    print("\n" + "=" * 70)
    print("3. 响应对象应该关注什么")
    print("=" * 70)
    sample = {
        "id": "chatcmpl-abc123",
        "model": "demo-model",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "这是一个示例回复。",
                },
            }
        ],
        "usage": {
            "prompt_tokens": 35,
            "completion_tokens": 42,
            "total_tokens": 77,
        },
    }
    print(json.dumps(sample, ensure_ascii=False, indent=2))
    print()
    print("你通常最关心这四部分：")
    print("1. choices[0].message.content -> 实际文本内容")
    print("2. choices[0].finish_reason -> 为什么停止")
    print("3. model -> 最终实际使用的模型")
    print("4. usage -> 输入 / 输出 / 总 token 消耗")


def run_call_demo(config: ProviderConfig, messages: list[dict[str, str]]) -> None:
    print("\n" + "=" * 70)
    print("4. 发起一次真实或模拟调用")
    print("=" * 70)

    # 这段函数的目标，是把“完整调用链路”明确地跑一遍：
    # 准备配置 -> 准备 messages -> 尝试真实调用 -> 失败时回退 mock ->
    # 打印 request_preview / response_preview / 最终文本内容。
    #
    # 其中最重要的认知有两个：
    # 1. 聊天不是一个黑盒窗口，而是一次结构化请求
    # 2. 代码真正消费的不是原始 HTTP 文本，而是整理后的响应对象
    if config.is_ready:
        try:
            # 有 API Key 时，优先走真实调用。
            # 真实调用内部会完成：
            # - 初始化 OpenAI-compatible client
            # - 调用 chat.completions.create()
            # - 提取 content / usage / 预览结构
            result = call_openai_compatible_chat(
                config=config,
                messages=messages,
                temperature=0.3,
                max_tokens=256,
            )
        except Exception as exc:
            # 教学脚本里保留自动回退，是为了保证“即使真实调用失败，
            # 也能继续把完整流程演示完”，避免学习在环境问题处卡死。
            print(f"真实调用失败：{type(exc).__name__}: {exc}")
            print("回退到 mock 模式，继续看完整链路。")
            result = mock_chat_response(config, messages, temperature=0.3, max_tokens=256)
    else:
        # 没有 API Key 时，不直接报错退出，而是用 mock 演示链路。
        # 这样你依然可以先理解请求体、响应结构和代码组织方式。
        print("未检测到 API Key，自动进入 mock 模式。")
        result = mock_chat_response(config, messages, temperature=0.3, max_tokens=256)

    # request_preview 代表“请求发出去之前，应用侧准备好的核心参数”。
    print("request_preview 请求参数:")
    print(json.dumps(result.request_preview or {}, ensure_ascii=False, indent=2))
    # response_preview 代表“从平台返回结果里，提炼出来的关键信息”。
    print("\nresponse_preview 返回结果:")
    print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))
    # result.content 才是大多数聊天产品最终会渲染给用户看的文本。
    print("\nassistant_content:")
    print(result.content)
    if result.usage:
        # usage 能帮助你理解这次调用的 token 消耗，也是后续成本统计的基础。
        print("\nusage:")
        print(json.dumps(result.usage.__dict__, ensure_ascii=False, indent=2))


def print_common_failures(config: ProviderConfig) -> None:
    print("\n" + "=" * 70)
    print("5. 常见失败点与排查顺序")
    print("=" * 70)
    print("常见错误类型：")
    print("- API Key 未配置或无效")
    print("- base_url 写错，指向了不兼容的地址")
    print("- model 名称写错")
    print("- 请求字段不被平台支持")
    print("- 网络问题 / 速率限制 / 服务端异常")
    print()
    print("建议排查顺序：")
    print(f"1. 先确认 provider={config.provider} 是否符合预期")
    print(f"2. 再确认 base_url={config.base_url or '(SDK 默认)'} 是否正确")
    print(f"3. 再确认 model={config.model} 是否存在")
    print("4. 最后再看是不是请求参数、网络、限流问题")


def main() -> None:
    # main 按教学顺序组织，不追求“封装最少”，而追求“每一步都能单独看懂”。
    #
    # 阅读这个函数时，可以按下面的顺序理解：
    # 1. 先把环境变量加载进来
    # 2. 再拿到当前 provider 配置
    # 3. 再准备本次调用要发送的 messages
    # 4. 然后依次打印：配置 -> 请求结构 -> 响应结构 -> 实际调用 -> 常见错误排查
    load_env_if_possible()
    config = load_provider_config()
    messages = build_demo_messages()

    print("第一条 LLM 请求：完整教学示例")
    print_config_summary(config)
    print_request_anatomy(config, messages)
    print_response_anatomy()
    run_call_demo(config, messages)
    print_common_failures(config)


if __name__ == "__main__":
    main()
