"""
llm_utils.py
第一章公共工具：环境变量、provider 配置、模型调用、token 估算、导出工具

这个文件的定位不是“业务入口”，而是给整章示例脚本提供公共能力。
可以把它理解成第一章的工具箱，主要解决 7 类问题：

1. 读取环境变量，决定当前用哪个 provider / model
2. 把不同平台的配置整理成统一的 ProviderConfig
3. 预览一次聊天请求大概会长什么样，方便教学和排查
4. 发起一次 OpenAI-compatible chat 调用
5. 在没有 API Key 或真实请求失败时，用 mock 结果继续演示完整链路
6. 估算文本 / messages 的 token 消耗，并支持简单裁剪
7. 把会话和元数据导出到本地 JSON 文件

阅读顺序建议：
load_provider_config()
-> preview_chat_request()
-> call_openai_compatible_chat()
-> mock_chat_response()

如果你第一次读代码，最值得先看的是 call_openai_compatible_chat()，
因为它最能体现“一次 LLM 调用到底发生了什么”。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20.0


def load_env_if_possible() -> None:
    """作用：
    尝试把 `.env` 中的环境变量加载到当前 Python 进程里。

    参数：
    无。函数会自动尝试导入 `python-dotenv`；如果没安装，就直接跳过，
    不会打断示例代码运行。
    """
    # 这里做的是“可选加载”：
    # 如果项目安装了 python-dotenv，就把 .env 读进当前进程环境变量；
    # 如果没有安装，也不要中断教学示例，因为用户仍然可能直接在系统环境里配置了变量。
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def _parse_float(value: str | None) -> float | None:
    """作用：
    把环境变量里读到的字符串安全地转换成 `float`。

    参数：
    value: 待转换的字符串，一般来自环境变量。
        - 传入 `None` 或空字符串时，返回 `None`
        - 传入合法数字字符串时，返回对应浮点数
        - 传入非法数字字符串时，返回 `None`
    """
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _get_request_timeout_seconds() -> float:
    """作用：
    获取真实 API 请求的超时时间，避免教学脚本在网络异常时长时间卡住。

    参数：
    无。函数会读取环境变量 `LLM_REQUEST_TIMEOUT_SECONDS`。
        - 如果配置了合法正数，就使用该值
        - 如果未配置、配置非法或小于等于 0，就回退到默认值

    返回：
    一个浮点数，表示请求超时秒数。
    """
    timeout = _parse_float(os.getenv("LLM_REQUEST_TIMEOUT_SECONDS"))
    if timeout is None or timeout <= 0:
        return DEFAULT_REQUEST_TIMEOUT_SECONDS
    return timeout


@dataclass
class ProviderConfig:
    # ProviderConfig 是“运行时平台配置”的统一抽象。
    # 上层脚本不需要关心当前是 OpenAI、DeepSeek 还是百炼，
    # 只需要拿到统一字段：api_key / base_url / model / price。
    provider: str
    api_key: str | None
    base_url: str | None
    model: str
    input_price_per_million: float | None = None
    output_price_per_million: float | None = None

    @property
    def is_ready(self) -> bool:
        """作用：
        判断当前 provider 配置是否满足“真实调用”的最小条件。

        参数：
        无。它直接检查当前对象里的 `api_key` 是否存在。
        一般用法是：
        - `True`：可以尝试真实调用
        - `False`：通常应回退到 mock 模式
        """
        return bool(self.api_key)


@dataclass
class ChatUsage:
    # ChatUsage 对齐响应里的 usage 结构。
    # 单独做成数据类，是为了让“原始 SDK 响应”和“教学层使用的统计对象”解耦。
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatResult:
    # ChatResult 是本章统一的“调用结果对象”。
    # 无论是真实调用还是 mock 调用，最终都整理成同一结构，
    # 这样上层示例代码就可以用同一套读取方式处理结果。
    provider: str
    model: str
    content: str
    usage: ChatUsage | None = None
    mocked: bool = False
    request_preview: dict[str, Any] | None = None
    raw_response_preview: dict[str, Any] | None = None


@dataclass
class ConversationExport:
    # 导出会话时，不直接裸写 messages，而是包一层带 provider / model / metadata 的结构，
    # 这样后续复盘时才知道这份导出文件是在什么上下文下生成的。
    provider: str
    model: str
    exported_at: str
    messages: list[dict[str, str]]
    metadata: dict[str, Any] = field(default_factory=dict)


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    """作用：
    从环境变量中读取指定 provider 的配置，并整理成统一的 `ProviderConfig`。

    参数：
    provider: 可选的 provider 名称。
        - 传入时，优先使用传入值，比如 `"openai"`、`"deepseek"`、`"bailian"`
        - 不传时，会读取 `DEFAULT_PROVIDER`
        - 如果两者都没有，就默认使用 `"openai"`

    返回：
    一个统一结构的 `ProviderConfig`，上层代码后续只依赖这个对象，
    不需要关心底层到底是哪一家平台。
    """
    # 先决定“当前要用哪个 provider”：
    # 1. 如果调用方显式传入 provider，就优先用传入值
    # 2. 否则读 DEFAULT_PROVIDER
    # 3. 再否则默认回到 openai
    provider_name = (provider or os.getenv("DEFAULT_PROVIDER", "openai")).strip().lower()

    # 这里不是在初始化 SDK，而是在做“环境变量 -> 统一配置对象”的映射。
    # 这样做的好处是：后续调用代码只依赖 ProviderConfig，
    # 不需要到处写 if provider == "xxx" 的分支。
    mapping = {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "input_price_per_million": _parse_float(os.getenv("OPENAI_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("OPENAI_OUTPUT_PRICE_PER_MILLION")),
        },
        "deepseek": {
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL"),
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "input_price_per_million": _parse_float(os.getenv("DEEPSEEK_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("DEEPSEEK_OUTPUT_PRICE_PER_MILLION")),
        },
        "bailian": {
            "api_key": os.getenv("BAILIAN_API_KEY"),
            "base_url": os.getenv("BAILIAN_BASE_URL"),
            "model": os.getenv("BAILIAN_MODEL", "qwen-plus"),
            "input_price_per_million": _parse_float(os.getenv("BAILIAN_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("BAILIAN_OUTPUT_PRICE_PER_MILLION")),
        },
        "glm": {
            "api_key": os.getenv("GLM_API_KEY"),
            "base_url": os.getenv("GLM_BASE_URL"),
            "model": os.getenv("GLM_MODEL", "glm-4.5-air"),
            "input_price_per_million": _parse_float(os.getenv("GLM_INPUT_PRICE_PER_MILLION")),
            "output_price_per_million": _parse_float(os.getenv("GLM_OUTPUT_PRICE_PER_MILLION")),
        },
    }

    data = mapping.get(provider_name, mapping["openai"])
    return ProviderConfig(provider=provider_name, **data)


def preview_chat_request(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    stop: list[str] | None = None,
) -> dict[str, Any]:
    """作用：
    生成一次聊天请求的预览数据，方便打印、教学展示和错误排查。

    参数：
    config: 当前 provider 配置对象，主要使用其中的 `model`。
    messages: 本次请求要发送的消息列表。
        通常按时间顺序组织，元素结构类似：
        `{"role": "user", "content": "你好"}`
    temperature: 输出发散程度。
        - 值越低，通常越稳定
        - 值越高，通常越发散
    max_tokens: 模型本次最多生成多少输出 token。
    stop: 可选的停止词列表。
        如果提供，模型遇到这些停止词时会提前结束输出。

    返回：
    一个普通字典，结构接近真实请求体，但不会真的发请求。
    """
    # 这个函数不发请求，只负责把“将要发送给模型的核心参数”整理出来。
    # 它的用途主要有两个：
    # 1. 教学：让学习者先看懂请求体长什么样
    # 2. 排查：调用失败时，能快速确认 model / messages / 参数是否符合预期
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if stop:
        payload["stop"] = stop
    return payload


def call_openai_compatible_chat(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 300,
    stop: list[str] | None = None,
) -> ChatResult:
    """作用：
    发起一次 OpenAI-compatible 聊天请求，并把响应整理成统一的 `ChatResult`。

    参数：
    config: 当前 provider 配置，包含 `api_key`、`base_url`、`model` 等信息。
        - `api_key` 用于认证
        - `base_url` 用于指定兼容平台地址
        - `model` 决定本次调用哪个模型
    messages: 本次请求的完整上下文消息列表。
        这通常是最关键的参数，里面包含 system、user、assistant 历史。
    temperature: 输出发散程度，默认 `0.3`。
        初学阶段可以理解为“越低越稳，越高越活”。
    max_tokens: 最大输出长度，默认 `300`。
        它只限制模型输出，不限制输入历史长度。
    stop: 可选停止词列表。
        适合结构化输出、固定格式输出等场景。

    返回：
    `ChatResult` 对象，里面统一放了：
    - 最终文本内容 `content`
    - token 用量 `usage`
    - 请求预览 `request_preview`
    - 响应预览 `raw_response_preview`
    """
    # 第 1 步：先生成 request_preview。
    # 这样即使后面真实调用失败，我们也依然能把“本来准备发送什么”展示出来。
    request_preview = preview_chat_request(config, messages, temperature, max_tokens, stop)

    try:
        from openai import APIConnectionError, APITimeoutError, OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    timeout_seconds = _get_request_timeout_seconds()

    # 第 2 步：初始化 OpenAI-compatible 客户端。
    # 这里的关键理解是：
    # - api_key 决定身份认证
    # - base_url 决定请求发往哪个兼容平台
    # - client 本身不代表已经发出请求，它只是一个“可发请求的客户端对象”
    #
    # 这里额外配置了 timeout 和 max_retries：
    # - timeout: 避免网络异常时脚本一直卡住
    # - max_retries=0: 教学脚本优先快速失败并回退 mock，而不是长时间重试
    client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=timeout_seconds,
        max_retries=0,
    )

    # 第 3 步：真正发起聊天请求。
    # 到这里，前面整理好的 model / messages / temperature / max_tokens
    # 才会作为一次结构化请求发送给模型服务。
    #
    # 这一步就是整条链路的核心：
    # 本地代码组织上下文 -> SDK 发起 HTTP 请求 -> 平台完成推理 -> 返回结构化响应对象。
    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stop=stop,
        )
    except APITimeoutError as exc:
        raise RuntimeError(
            f"LLM 请求超时（>{timeout_seconds:.0f}s）。"
            "请检查网络、base_url 或 provider 服务状态；脚本可回退到 mock 模式继续演示。"
        ) from exc
    except APIConnectionError as exc:
        raise RuntimeError(
            "LLM 连接失败。请检查网络、base_url 是否正确，以及当前平台服务是否可访问。"
        ) from exc

    # 第 4 步：从原始响应里抽取 usage。
    # 注意：应用开发里通常不会把整个 SDK 响应对象到处传，
    # 而是只提取自己后续要关心的那部分信息。
    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    # 第 5 步：从 choices[0] 中提取本次最主要的结果。
    # 初学阶段先建立一个直觉：
    # 你最常读取的是 choices[0].message.content，
    # 另外 finish_reason 可以帮助你判断输出为什么结束。
    message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason

    # 第 6 步：把“教学最需要看的响应关键信息”整理成 preview。
    # 这样上层脚本打印出来时，比直接打印完整 SDK 对象更清晰，也更稳定。
    raw_response_preview = {
        "id": response.id,
        "model": response.model,
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {
                    "role": message.role,
                    "content": message.content,
                },
            }
        ],
        "usage": asdict(usage) if usage else None,
    }

    # 第 7 步：封装成统一 ChatResult 返回给上层。
    # 上层脚本接下来只需要关心：
    # - result.content       给用户显示什么
    # - result.usage         这次消耗了多少 token
    # - result.request_preview / raw_response_preview
    #                        教学展示和错误排查时打印什么
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=message.content or "",
        usage=usage,
        mocked=False,
        request_preview=request_preview,
        raw_response_preview=raw_response_preview,
    )


def mock_chat_response(
    config: ProviderConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 300,
) -> ChatResult:
    """作用：
    构造一个模拟聊天结果，在没有 API Key 或真实调用失败时继续演示完整流程。

    参数：
    config: 当前 provider 配置，用于在 mock 结果里保留 provider / model 信息。
    messages: 当前请求上下文。
        函数会从中提取：
        - 第一条 system 消息，用来展示当前助手设定
        - 最后一条 user 消息，用来展示用户最后一次输入
    temperature: 本次请求原本准备使用的温度参数。
        mock 不做真实推理，但会把该参数展示出来，方便教学观察。
    max_tokens: 本次请求原本准备使用的最大输出长度。
        同样会写入 mock 内容里，便于查看参数传递链路。

    返回：
    一个结构与真实调用一致的 `ChatResult`，区别只是 `mocked=True`。
    """
    # mock 的目标不是“模拟真实模型能力”，而是模拟“返回结构”。
    # 这样在没有 API Key 的情况下，学习者也能把完整代码链路先跑通。
    last_user = ""
    system_prompt = ""
    for item in messages:
        if item["role"] == "system" and not system_prompt:
            system_prompt = item["content"]
    for item in reversed(messages):
        if item["role"] == "user":
            last_user = item["content"]
            break

    content = (
        # mock 输出刻意把关键上下文拼进文本里，
        # 是为了让学习者直接看到：当前请求到底带了什么历史和参数。
        f"[MOCK:{config.provider}] 你最后一次提问是：{last_user}\n"
        f"当前 system prompt 摘要：{system_prompt[:40] or '（无）'}\n"
        f"temperature={temperature}, max_tokens={max_tokens}"
    )
    return ChatResult(
        provider=config.provider,
        model=config.model,
        content=content,
        mocked=True,
        request_preview=preview_chat_request(config, messages, temperature, max_tokens),
        raw_response_preview={
            "id": "mock-chatcmpl-001",
            "model": config.model,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": None,
        },
    )


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """作用：
    估算一段文本大约会占用多少 token。

    参数：
    text: 要估算的文本内容，可以是中文、英文或混合文本。
    encoding_name: 使用哪种 tokenizer 编码规则，默认 `cl100k_base`。
        - 如果本地安装了 `tiktoken`，会按指定编码做更准确估算
        - 如果没安装，会回退到启发式估算

    返回：
    一个整数，表示估算出的 token 数量。
    """
    try:
        import tiktoken
    except ImportError:
        # 没安装 tiktoken 时，退回启发式估算。
        # 它不精确，但足够帮助初学者建立“文本越长，token 越多”的量感。
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        non_ascii_chars = len(text) - ascii_chars
        english_est = max(1, ascii_chars // 4) if ascii_chars else 0
        chinese_est = max(1, int(non_ascii_chars / 1.5)) if non_ascii_chars else 0
        return english_est + chinese_est

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def estimate_messages_tokens(messages: list[dict[str, str]], encoding_name: str = "cl100k_base") -> int:
    """作用：
    估算整个 `messages` 列表作为输入上下文时，大约会消耗多少 token。

    参数：
    messages: 消息列表。
        每条消息通常包含：
        - `role`：消息角色，比如 `system`、`user`、`assistant`
        - `content`：消息正文
    encoding_name: 使用哪种 tokenizer 编码规则，默认 `cl100k_base`。

    返回：
    一个整数，表示整段消息历史的估算 token 数。
    """
    # messages 的 token 成本不只是 content。
    # role、自身的消息包装开销，也会占用 token。
    total = 0
    for item in messages:
        total += estimate_tokens(item["role"], encoding_name)
        total += estimate_tokens(item["content"], encoding_name)
        total += 4
    return total + 2


def trim_messages_by_recent_messages(
    messages: list[dict[str, str]],
    keep_last_messages: int = 6,
) -> list[dict[str, str]]:
    """作用：
    按“最近消息条数”裁剪历史，同时始终保留 system 消息。

    参数：
    messages: 原始消息历史列表。
    keep_last_messages: 要保留的最近非 system 消息条数，默认 `6`。
        例如传入 `6`，就表示：
        - 所有 system 消息保留
        - 其余消息只保留最后 6 条

    返回：
    裁剪后的新消息列表。
    """
    # 这是最简单、最适合第一章的裁剪策略：
    # 永远保留 system，再保留最近 N 条非 system 消息。
    # 好处是实现简单、行为稳定，适合先建立上下文管理的基本认知。
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    return system_messages + others[-keep_last_messages:]


def trim_messages_by_token_budget(
    messages: list[dict[str, str]],
    max_input_tokens: int,
    encoding_name: str = "cl100k_base",
) -> list[dict[str, str]]:
    """作用：
    按输入 token 预算裁剪历史，尽量保留最新消息，同时始终保留 system 消息。

    参数：
    messages: 原始消息历史列表。
    max_input_tokens: 本次请求允许占用的最大输入 token 预算。
        函数会从最新消息开始倒着尝试加入，直到超预算为止。
    encoding_name: 使用哪种 tokenizer 编码规则，默认 `cl100k_base`。

    返回：
    在不超过 `max_input_tokens` 的前提下，尽量保留更多最近消息的新列表。
    """
    # 这个版本不是按“消息条数”裁剪，而是按“token 预算”裁剪。
    # 实现思路是：从最新消息开始倒着尝试保留，直到再加入一条就超预算为止。
    system_messages = [item for item in messages if item["role"] == "system"]
    others = [item for item in messages if item["role"] != "system"]
    result = list(system_messages)

    for item in reversed(others):
        # candidate 表示“如果把这条历史也保留下来，整个请求会变成什么样”。
        candidate = system_messages + [item] + result[len(system_messages):]
        if estimate_messages_tokens(candidate, encoding_name) <= max_input_tokens:
            result = system_messages + [item] + result[len(system_messages):]
        else:
            break
    return result


def calculate_cost_from_usage(
    usage: ChatUsage | None,
    input_price_per_million: float | None,
    output_price_per_million: float | None,
) -> float | None:
    """作用：
    根据 usage 和单价，估算一次调用的大致成本。

    参数：
    usage: 本次调用的 token 用量。
        如果为 `None`，说明当前没有可计算的 usage，函数会直接返回 `None`。
    input_price_per_million: 输入单价，单位是“每百万 token 多少钱”。
    output_price_per_million: 输出单价，单位是“每百万 token 多少钱”。

    返回：
    - 如果 usage 和价格都齐全，返回估算成本 `float`
    - 如果任何一个关键值缺失，返回 `None`
    """
    # 成本估算公式本身很直接：
    # 输入 token 按输入单价计费，输出 token 按输出单价计费，最后相加。
    if not usage or input_price_per_million is None or output_price_per_million is None:
        return None
    input_cost = usage.prompt_tokens / 1_000_000 * input_price_per_million
    output_cost = usage.completion_tokens / 1_000_000 * output_price_per_million
    return input_cost + output_cost


def format_cost(cost: float | None) -> str:
    """作用：
    把成本数值格式化成更适合打印展示的字符串。

    参数：
    cost: 成本数值。
        - 传入浮点数时，格式化为美元字符串
        - 传入 `None` 时，说明还没有可用价格配置

    返回：
    格式化后的成本文本，比如 `$0.000123` 或 `未配置价格`。
    """
    if cost is None:
        return "未配置价格"
    return f"${cost:.6f}"


def ensure_export_dir() -> Path:
    """作用：
    确保会话导出目录存在，如果不存在就自动创建。

    参数：
    无。函数内部固定使用模块级常量 `EXPORT_DIR`。

    返回：
    导出目录对应的 `Path` 对象，方便后续继续拼接文件名。
    """
    # 导出前先确保目录存在，避免调用方每次都关心文件系统初始化。
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return EXPORT_DIR


def export_conversation(
    provider: str,
    model: str,
    messages: list[dict[str, str]],
    metadata: dict[str, Any] | None = None,
) -> Path:
    """作用：
    把当前会话历史和附加元数据导出为本地 JSON 文件。

    参数：
    provider: 本次会话所属平台名，用于写入导出文件元信息。
    model: 本次会话使用的模型名，用于后续复盘。
    messages: 要导出的消息历史列表。
        通常就是应用侧当前保存的完整上下文快照。
    metadata: 可选附加信息。
        常见用法包括记录：
        - 对话轮数
        - token 统计
        - 当前实验标签

    返回：
    导出后的文件路径 `Path`，调用方可以直接打印给用户查看。
    """
    # 导出的不是“模型内部记忆”，而是应用侧维护的 messages 快照。
    # 这也是多轮对话一个非常关键的工程认知：历史是你自己存的，不是模型替你存的。
    export_dir = ensure_export_dir()
    filename = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = export_dir / filename
    payload = ConversationExport(
        provider=provider,
        model=model,
        exported_at=datetime.now().isoformat(),
        messages=messages,
        metadata=metadata or {},
    )
    path.write_text(json.dumps(asdict(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path
