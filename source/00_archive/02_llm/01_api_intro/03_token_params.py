"""
03_token_params.py
Token、上下文窗口、成本估算、参数实验建议

运行方式：
    python 03_token_params.py

依赖：
    pip install tiktoken
"""

from __future__ import annotations

from llm_utils import (
    ChatUsage,
    calculate_cost_from_usage,
    estimate_messages_tokens,
    estimate_tokens,
    format_cost,
    trim_messages_by_recent_messages,
    trim_messages_by_token_budget,
)


TEXT_SAMPLES = {
    # 这里故意放中文、英文、中英混合三种文本，
    # 是为了帮助学习者建立“不同文本形态的 token 密度不一样”的直觉。
    "中文短句": "人工智能正在改变世界。",
    "英文短句": "Artificial intelligence is changing the world.",
    "中英混合": "AI 应用开发需要 prompt, context, tools 和 engineering。",
    "长提示词": "你是一个专业的技术顾问，请结合下面的上下文，输出结构化建议，并控制在 200 字以内。",
}


def print_token_comparison() -> None:
    print("=" * 70)
    print("1. 不同文本的 Token 对比")
    print("=" * 70)
    for label, text in TEXT_SAMPLES.items():
        cl100k = estimate_tokens(text, "cl100k_base")
        try:
            o200k = estimate_tokens(text, "o200k_base")
        except Exception:
            o200k = cl100k
        print(f"{label:8s} | cl100k_base={cl100k:3d} | o200k_base={o200k:3d}")
        print(f"         文本：{text}")


def print_message_budget_demo() -> None:
    # 这个示例不是追求真实业务数据，而是构造一段“会明显变长的历史”，
    # 方便你观察两种裁剪策略的结果差异。
    messages = [
        {"role": "system", "content": "你是一个有帮助的 AI 助手。"},
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，有什么可以帮助你的？"},
        {"role": "user", "content": "我正在做一个 AI 聊天产品。"},
        {"role": "assistant", "content": "很好，多轮对话、结构化输出、流式响应都会用到。"},
        {"role": "user", "content": "我需要保存历史消息吗？"},
        {"role": "assistant", "content": "需要，因为模型不会天然记住上一轮内容。"},
        {"role": "user", "content": "那上下文越来越长怎么办？"},
        {"role": "assistant", "content": "常见做法是裁剪历史、摘要压缩、分层记忆。"},
        {"role": "user", "content": "第一章我至少应该先掌握哪种裁剪方案？"},
    ]

    print("\n" + "=" * 70)
    print("2. 上下文预算与裁剪")
    print("=" * 70)
    total = estimate_messages_tokens(messages)
    print(f"原始消息数: {len(messages)}")
    print(f"原始估算输入 tokens: {total}")

    # 第一种方式按消息条数裁剪，规则简单，适合第一章先掌握。
    trimmed_recent = trim_messages_by_recent_messages(messages, keep_last_messages=4)
    trimmed_recent_tokens = estimate_messages_tokens(trimmed_recent)
    print(f"\n按最近消息裁剪后 tokens: {trimmed_recent_tokens}")
    for item in trimmed_recent:
        print(f"- {item['role']}: {item['content']}")

    # 第二种方式按 token 预算裁剪，更接近真实线上系统的控制方式。
    trimmed_budget = trim_messages_by_token_budget(messages, max_input_tokens=70)
    trimmed_budget_tokens = estimate_messages_tokens(trimmed_budget)
    print(f"\n按 token 预算裁剪后 tokens: {trimmed_budget_tokens}")
    for item in trimmed_budget:
        print(f"- {item['role']}: {item['content']}")

    print("\n关键理解：")
    print("1. 多轮对话成本主要来自历史消息不断累积")
    print("2. 最简单的工程方案通常是：保留 system + 最近若干轮")
    print("3. 真正上线后才会继续引入摘要压缩、长期记忆等高级策略")


def print_cost_demo() -> None:
    print("\n" + "=" * 70)
    print("3. 成本估算")
    print("=" * 70)
    # 这里不直接绑定某个平台的最新价格，
    # 是因为平台定价会变化，而这一章更重要的是先理解成本计算公式。
    print("这里不写死真实平台当前价格，而是演示公式。")
    print("请按你实际平台控制台价格替换。")

    usage = ChatUsage(prompt_tokens=1200, completion_tokens=400, total_tokens=1600)
    input_price_per_million = 0.8
    output_price_per_million = 2.0
    cost = calculate_cost_from_usage(usage, input_price_per_million, output_price_per_million)

    print(f"示例 usage: {usage}")
    print(f"输入价格（每百万 tokens）: ${input_price_per_million}")
    print(f"输出价格（每百万 tokens）: ${output_price_per_million}")
    print(f"单次调用成本: {format_cost(cost)}")
    if cost is not None:
        print(f"1000 次类似调用成本: ${cost * 1000:.4f}")


def print_parameter_guide() -> None:
    print("\n" + "=" * 70)
    print("4. 常用参数如何选")
    print("=" * 70)
    presets = [
        ("代码生成", {"temperature": 0.1, "max_tokens": 800, "reason": "追求稳定、少发散"}),
        ("结构化提取", {"temperature": 0.0, "max_tokens": 300, "reason": "优先格式稳定和字段一致"}),
        ("通用问答", {"temperature": 0.4, "max_tokens": 500, "reason": "在稳定和自然之间平衡"}),
        ("创意写作", {"temperature": 0.9, "max_tokens": 1000, "reason": "允许发散和表达变化"}),
    ]
    for task, params in presets:
        print(f"{task}: {params}")

    print("\n参数理解建议：")
    print("- temperature: 控制发散程度，不是“越低越好”")
    print("- top_p: 与 temperature 作用相近，初学阶段通常先调一个")
    print("- max_tokens: 控制输出上限，也影响成本和延迟")
    print("- stop: 适合列表生成、固定分隔符输出等场景")
    print("- presence_penalty / frequency_penalty: 初学阶段先知道存在即可")


def print_parameter_experiment_design() -> None:
    prompt = "请写一句关于春天和编程的短句。"
    print("\n" + "=" * 70)
    print("5. 如何设计参数实验")
    print("=" * 70)
    print(f"固定 prompt: {prompt}")
    # 这一段是在讲实验方法，而不是推荐某个固定参数。
    # 初学者最容易犯的错，就是同时改 prompt、temperature、max_tokens，
    # 结果最后无法判断到底是哪一个变量导致输出变化。
    print("建议实验方式：")
    print("1. 固定 prompt，不改任何上下文")
    print("2. 只改 temperature = 0 / 0.5 / 1.0")
    print("3. 对比输出是否更稳定、更发散")
    print("4. 再尝试加入 max_tokens 限制，观察输出长度变化")
    print()
    print("不要同时改多个参数，否则你很难知道到底是谁在起作用。")


def main() -> None:
    # 这个脚本本质上是一个“参数与成本观察台”：
    # 依次建立 token 感知、上下文预算感知、成本公式感知和参数实验方法。
    print_token_comparison()
    print_message_budget_demo()
    print_cost_demo()
    print_parameter_guide()
    print_parameter_experiment_design()


if __name__ == "__main__":
    main()
