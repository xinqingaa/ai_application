"""
04_chat_cli.py
最小可用聊天 CLI：多轮历史、参数查看、裁剪、导出、统计

运行方式：
    python 04_chat_cli.py

依赖：
    pip install openai python-dotenv tiktoken
"""

from __future__ import annotations

from dataclasses import dataclass, field

from llm_utils import (
    ChatUsage,
    call_openai_compatible_chat,
    calculate_cost_from_usage,
    estimate_messages_tokens,
    export_conversation,
    format_cost,
    load_env_if_possible,
    load_provider_config,
    mock_chat_response,
    trim_messages_by_recent_messages,
)


@dataclass
class SessionStats:
    # SessionStats 只做一件事：累计整场会话的 usage。
    # 它和 ConversationState 分开，是为了把“消息历史”和“统计数据”拆成两类状态。
    rounds: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add_usage(self, usage: ChatUsage | None) -> None:
        # mock 模式或某些异常情况下可能没有 usage，这里直接跳过。
        if not usage:
            return
        self.prompt_tokens += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens


@dataclass
class ConversationState:
    # ConversationState 维护“当前会话上下文”。
    # 之后每次调用模型时，真正发出去的 messages 都来自这里。
    system_prompt: str
    keep_last_messages: int = 8
    messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # 会话初始化时就放入 system prompt，
        # 这样后续任何一轮请求都默认带着统一助手设定。
        self.messages.append({"role": "system", "content": self.system_prompt})

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def clear(self) -> None:
        # clear 不是把 messages 清空，而是回到“只剩 system prompt”的初始状态。
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def set_system_prompt(self, text: str) -> None:
        # 这里直接改 messages[0]，是因为本例约定第 0 条始终是 system 消息。
        self.system_prompt = text
        self.messages[0] = {"role": "system", "content": text}

    def trim(self) -> None:
        # 裁剪动作发生在应用侧，而不是模型侧。
        self.messages = trim_messages_by_recent_messages(self.messages, self.keep_last_messages)


def print_help() -> None:
    print(
        """
可用命令：
  /help                     查看帮助
  /history                  打印当前历史消息
  /clear                    清空历史，只保留 system prompt
  /model <name>             切换模型名
  /system <text>            修改 system prompt
  /params                   查看当前参数配置
  /trim <n>                 只保留最近 n 条非 system 消息
  /stats                    查看本轮累计 token 和成本
  /export                   导出当前会话为 JSON
  /mock on|off              强制开启或关闭 mock 模式
  /quit                     退出
"""
    )


def print_history(state: ConversationState) -> None:
    print("=" * 70)
    print("当前历史消息")
    print("=" * 70)
    for index, item in enumerate(state.messages, start=1):
        print(f"[{index}] {item['role']}: {item['content']}")
    print(f"\n当前估算输入 tokens: {estimate_messages_tokens(state.messages)}")


def print_stats(stats: SessionStats, input_price: float | None, output_price: float | None) -> None:
    usage = ChatUsage(
        prompt_tokens=stats.prompt_tokens,
        completion_tokens=stats.completion_tokens,
        total_tokens=stats.total_tokens,
    )
    cost = calculate_cost_from_usage(usage, input_price, output_price)
    print("=" * 70)
    print("会话统计")
    print("=" * 70)
    print(f"rounds: {stats.rounds}")
    print(f"prompt_tokens: {stats.prompt_tokens}")
    print(f"completion_tokens: {stats.completion_tokens}")
    print(f"total_tokens: {stats.total_tokens}")
    print(f"estimated_cost: {format_cost(cost)}")


def handle_command(
    raw: str,
    config,
    state: ConversationState,
    stats: SessionStats,
    force_mock: dict[str, bool],
) -> bool:
    # handle_command 的作用是把“控制类输入”和“正常聊天输入”分流。
    # 返回 True 表示这是一条命令，主循环不需要再把它发给模型。
    if raw == "/help":
        print_help()
        return True
    if raw == "/history":
        print_history(state)
        return True
    if raw == "/clear":
        state.clear()
        print("历史已清空。")
        return True
    if raw.startswith("/model "):
        model = raw.replace("/model ", "", 1).strip()
        if not model:
            print("请输入模型名，例如：/model qwen-plus")
        else:
            config.model = model
            print(f"当前模型已切换为：{config.model}")
        return True
    if raw.startswith("/system "):
        text = raw.replace("/system ", "", 1).strip()
        if not text:
            print("请输入新的 system prompt。")
        else:
            state.set_system_prompt(text)
            print("system prompt 已更新。")
        return True
    if raw == "/params":
        print("=" * 70)
        print("当前参数")
        print("=" * 70)
        print(f"provider: {config.provider}")
        print(f"base_url: {config.base_url or '(SDK 默认)'}")
        print(f"model: {config.model}")
        print(f"temperature: 0.3")
        print(f"max_tokens: 400")
        print(f"keep_last_messages: {state.keep_last_messages}")
        print(f"mock_mode: {force_mock['enabled']}")
        return True
    if raw.startswith("/trim "):
        value = raw.replace("/trim ", "", 1).strip()
        try:
            keep_last_messages = int(value)
        except ValueError:
            print("请输入整数，例如：/trim 6")
            return True
        state.keep_last_messages = keep_last_messages
        state.trim()
        print(f"已裁剪历史，仅保留最近 {keep_last_messages} 条非 system 消息。")
        return True
    if raw == "/stats":
        print_stats(stats, config.input_price_per_million, config.output_price_per_million)
        return True
    if raw == "/export":
        path = export_conversation(
            provider=config.provider,
            model=config.model,
            messages=state.messages,
            metadata={
                "rounds": stats.rounds,
                "prompt_tokens": stats.prompt_tokens,
                "completion_tokens": stats.completion_tokens,
                "total_tokens": stats.total_tokens,
            },
        )
        print(f"已导出到：{path}")
        return True
    if raw == "/mock on":
        force_mock["enabled"] = True
        print("已开启强制 mock 模式。")
        return True
    if raw == "/mock off":
        force_mock["enabled"] = False
        print("已关闭强制 mock 模式。")
        return True
    if raw == "/quit":
        raise KeyboardInterrupt
    return False


def main() -> None:
    # main 体现了一个最小聊天应用的完整工作流：
    # 初始化环境和配置 -> 创建会话状态 -> 循环读取用户输入 ->
    # 命令分流或模型调用 -> 更新历史和统计 -> 打印结果。
    load_env_if_possible()
    config = load_provider_config()
    state = ConversationState(
        system_prompt="你是一个 AI 应用开发学习助手，回答要简洁，优先使用应用开发视角。"
    )
    stats = SessionStats()
    # 默认行为是：如果没配置 API Key，就直接进入 mock 模式，
    # 保证这个 CLI 即使离线学习也能把完整流程跑通。
    force_mock = {"enabled": not config.is_ready}

    print("=" * 70)
    print("最小可用聊天 CLI")
    print("=" * 70)
    print(f"provider: {config.provider}")
    print(f"base_url: {config.base_url or '(SDK 默认)'}")
    print(f"model: {config.model}")
    print("输入 /help 查看命令。")
    if force_mock["enabled"]:
        print("当前将使用 mock 模式。配置 API Key 后可切换到真实调用。")

    while True:
        try:
            raw = input("\n> ").strip()
            if not raw:
                continue

            # 先判断是不是命令；命令只修改本地状态或打印信息，不发给模型。
            if raw.startswith("/"):
                if handle_command(raw, config, state, stats, force_mock):
                    continue

            # 走到这里，说明这是一条正常聊天消息。
            # 先把用户输入写入历史，再基于当前历史生成本次请求上下文。
            state.add_user(raw)
            messages = list(state.messages)

            if not force_mock["enabled"]:
                try:
                    # 真实调用时，messages 就是本轮完整上下文：
                    # system + 过去历史 + 当前用户新输入。
                    result = call_openai_compatible_chat(
                        config=config,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=400,
                    )
                except Exception as exc:
                    # 真实调用失败后自动回退 mock，是为了保持 CLI 可继续使用，
                    # 也让学习者能继续观察完整状态流转。
                    print(f"真实调用失败：{type(exc).__name__}: {exc}")
                    print("自动回退到 mock 模式。")
                    force_mock["enabled"] = True
                    result = mock_chat_response(config, messages, temperature=0.3, max_tokens=400)
            else:
                result = mock_chat_response(config, messages, temperature=0.3, max_tokens=400)

            # 模型返回后，要把 assistant 回复也写回历史。
            # 这一步非常关键，因为下一轮对话是否“记得刚才说过什么”，
            # 就取决于你有没有把这条 assistant 消息继续带上。
            state.add_assistant(result.content)
            stats.rounds += 1
            stats.add_usage(result.usage)

            print(f"AI: {result.content}")
            if result.usage:
                print(f"[usage] {result.usage.__dict__}")

            # 每轮结束后重新估算当前历史大小，
            # 是为了让你观察“多轮对话为什么会越来越贵”。
            estimated_input_tokens = estimate_messages_tokens(state.messages)
            print(f"[history_estimated_tokens] {estimated_input_tokens}")

        except KeyboardInterrupt:
            print("\n已退出聊天。")
            break


if __name__ == "__main__":
    main()
