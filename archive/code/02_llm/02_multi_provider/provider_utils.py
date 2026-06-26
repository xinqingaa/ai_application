"""
provider_utils.py
第二章公共工具：provider 注册表、能力矩阵、请求预览、统一响应结构、最小统一客户端

这个文件不是某个演示脚本的入口，而是第二章所有示例共享的“底层工具箱”。
它主要负责 6 类事情：

1. 维护 provider 注册表，集中描述默认模型、默认 base_url 和能力矩阵
2. 把环境变量整理成统一的 `ProviderConfig`
3. 根据 provider 类型构造不同风格的请求预览
4. 为 OpenAI-compatible 平台发起真实调用
5. 在环境未就绪或调用失败时提供 mock 回退
6. 对外提供一个最小统一客户端 `UnifiedLLMClient`

阅读顺序建议：
PROVIDER_REGISTRY
-> load_provider_config()
-> build_provider_preview()
-> call_openai_compatible_chat()
-> UnifiedLLMClient.chat()
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any


def load_env_if_possible() -> None:
    """作用：
    尝试加载 `.env` 环境变量，减少教学脚本的环境准备成本。

    参数：
    无。函数会尝试导入 `python-dotenv`；如果本地未安装，则直接跳过。
    """
    # 这里保持“可选加载”：
    # 装了 python-dotenv 就读 .env；没装也不影响代码继续运行。
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


@dataclass
class ProviderCapabilities:
    """描述某个 provider 的能力矩阵。

    这层信息的作用是把“平台支持什么、不支持什么”显式放到配置层，
    避免业务代码到处猜测平台行为。
    """

    openai_compatible: bool
    supports_system_role_inline: bool
    supports_separate_system_prompt: bool
    supports_streaming: bool
    supports_native_structured_output: bool
    supports_vision: bool


@dataclass
class ProviderProfile:
    """注册表里的静态 provider 描述。

    `ProviderProfile` 偏“课程配置模板”：
    - 描述默认值
    - 描述环境变量名
    - 描述文档中的角色定位

    它还不是运行时配置；运行时真正使用的是 `ProviderConfig`。
    """

    key: str
    display_name: str
    provider_type: str
    api_key_env: str | None
    base_url_env: str | None
    model_env: str | None
    default_base_url: str | None
    default_model: str
    docs_role: str
    notes: str
    capabilities: ProviderCapabilities


@dataclass
class ProviderConfig:
    """运行时 provider 配置对象。

    上层示例代码通常不直接读取环境变量，而是统一依赖这个对象，
    这样业务层就不用关心具体平台的环境变量命名差异。
    """

    key: str
    display_name: str
    provider_type: str
    api_key: str | None
    base_url: str | None
    model: str
    capabilities: ProviderCapabilities
    notes: str

    @property
    def is_ready(self) -> bool:
        """作用：
        判断当前 provider 配置是否满足“尝试真实调用”的基本条件。

        参数：
        无。函数直接检查当前对象中的认证信息和关键连接信息。

        返回：
        `True` 表示可以尝试真实调用，`False` 表示更适合回退到 mock 模式。
        """
        if self.provider_type == "openai_compatible":
            return bool(self.api_key and self.base_url and self.model)
        return bool(self.api_key)


@dataclass
class ChatRequest:
    """统一聊天请求对象。

    第二章的关键约束之一就是：统一抽象必须保留 `messages` 级输入，
    而不是退化成单个 prompt 字符串。
    """

    messages: list[dict[str, str]]
    temperature: float = 0.3
    max_tokens: int = 300
    stop: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatUsage:
    """统一的 token 用量结构。

    这样做的目的是让上层代码不直接耦合底层 SDK 的 usage 对象结构。
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class NormalizedChatResponse:
    """统一聊天响应对象。

    无论真实调用还是 mock 调用，最终都整理成同一结构，
    这样示例脚本可以用同一套方式打印 content、usage 和调试信息。
    """

    provider: str
    model: str
    content: str
    usage: ChatUsage | None = None
    finish_reason: str | None = None
    request_preview: dict[str, Any] | None = None
    raw_response_preview: dict[str, Any] | None = None
    mocked: bool = False
    elapsed_ms: float | None = None
    error: str | None = None


# PROVIDER_REGISTRY 是第二章配置层的“单一事实来源”。
# 新增 provider 时，优先先补这里，再让下游函数消费统一定义。
PROVIDER_REGISTRY: dict[str, ProviderProfile] = {
    "openai": ProviderProfile(
        key="openai",
        display_name="OpenAI",
        provider_type="openai_compatible",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        model_env="OPENAI_MODEL",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        docs_role="国际主流接口参考",
        notes="作为 OpenAI 风格接口主线参考，生态最成熟。",
        capabilities=ProviderCapabilities(
            openai_compatible=True,
            supports_system_role_inline=True,
            supports_separate_system_prompt=False,
            supports_streaming=True,
            supports_native_structured_output=True,
            supports_vision=True,
        ),
    ),
    "deepseek": ProviderProfile(
        key="deepseek",
        display_name="DeepSeek",
        provider_type="openai_compatible",
        api_key_env="DEEPSEEK_API_KEY",
        base_url_env="DEEPSEEK_BASE_URL",
        model_env="DEEPSEEK_MODEL",
        default_base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
        docs_role="国内低成本实践",
        notes="高性价比，适合大多数学习和实验场景。",
        capabilities=ProviderCapabilities(
            openai_compatible=True,
            supports_system_role_inline=True,
            supports_separate_system_prompt=False,
            supports_streaming=True,
            supports_native_structured_output=False,
            supports_vision=False,
        ),
    ),
    "bailian": ProviderProfile(
        key="bailian",
        display_name="Bailian / Qwen",
        provider_type="openai_compatible",
        api_key_env="BAILIAN_API_KEY",
        base_url_env="BAILIAN_BASE_URL",
        model_env="BAILIAN_MODEL",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        docs_role="国内主练平台",
        notes="国内可用性和实践友好度很高，适合课程实验。",
        capabilities=ProviderCapabilities(
            openai_compatible=True,
            supports_system_role_inline=True,
            supports_separate_system_prompt=False,
            supports_streaming=True,
            supports_native_structured_output=False,
            supports_vision=True,
        ),
    ),
    "glm": ProviderProfile(
        key="glm",
        display_name="GLM",
        provider_type="openai_compatible",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
        model_env="GLM_MODEL",
        default_base_url="https://open.bigmodel.cn/api/paas/v4/",
        default_model="glm-4.5-air",
        docs_role="国产平台横向对比",
        notes="常见国产模型平台，适合做 provider 切换练习。",
        capabilities=ProviderCapabilities(
            openai_compatible=True,
            supports_system_role_inline=True,
            supports_separate_system_prompt=False,
            supports_streaming=True,
            supports_native_structured_output=False,
            supports_vision=True,
        ),
    ),
    "claude": ProviderProfile(
        key="claude",
        display_name="Claude",
        provider_type="anthropic_style",
        api_key_env="ANTHROPIC_API_KEY",
        base_url_env=None,
        model_env="ANTHROPIC_MODEL",
        default_base_url="https://api.anthropic.com/v1",
        default_model="claude-sonnet-4-0",
        docs_role="差异化接口参考",
        notes="system 通常单独传递，结构化输出思路与 OpenAI 有差异。",
        capabilities=ProviderCapabilities(
            openai_compatible=False,
            supports_system_role_inline=False,
            supports_separate_system_prompt=True,
            supports_streaming=True,
            supports_native_structured_output=False,
            supports_vision=True,
        ),
    ),
    "gemini": ProviderProfile(
        key="gemini",
        display_name="Gemini",
        provider_type="google_style",
        api_key_env="GEMINI_API_KEY",
        base_url_env=None,
        model_env="GEMINI_MODEL",
        default_base_url="https://generativelanguage.googleapis.com",
        default_model="gemini-2.5-pro",
        docs_role="多模态与接口差异参考",
        notes="内容对象组织方式和 SDK 形态与 OpenAI、Anthropic 不同。",
        capabilities=ProviderCapabilities(
            openai_compatible=False,
            supports_system_role_inline=False,
            supports_separate_system_prompt=False,
            supports_streaming=True,
            supports_native_structured_output=False,
            supports_vision=True,
        ),
    ),
}


def list_registered_providers() -> list[str]:
    """作用：
    返回当前注册表里的 provider 键列表。

    参数：
    无。函数直接读取模块级 `PROVIDER_REGISTRY`。

    返回：
    provider 名称列表，例如 `["openai", "deepseek", "bailian"]`。
    """
    return list(PROVIDER_REGISTRY.keys())


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    """作用：
    从 provider 注册表和环境变量中生成运行时 `ProviderConfig`。

    参数：
    provider: 可选的 provider 名称。
        - 传入时，优先使用传入值
        - 不传时，读取 `DEFAULT_PROVIDER`
        - 如果两者都没有，就回退到 `bailian`

    返回：
    一个统一结构的 `ProviderConfig`，供请求构建层和统一客户端继续使用。
    """
    # 先决定当前使用哪个 provider，再从注册表里取出“静态模板”。
    key = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    profile = PROVIDER_REGISTRY.get(key, PROVIDER_REGISTRY["bailian"])
    # 再把环境变量覆盖到运行时配置中，形成真正可用于调用的对象。
    api_key = os.getenv(profile.api_key_env) if profile.api_key_env else None
    base_url = (
        os.getenv(profile.base_url_env) if profile.base_url_env else profile.default_base_url
    ) or profile.default_base_url
    model = os.getenv(profile.model_env, profile.default_model) if profile.model_env else profile.default_model
    return ProviderConfig(
        key=profile.key,
        display_name=profile.display_name,
        provider_type=profile.provider_type,
        api_key=api_key,
        base_url=base_url,
        model=model,
        capabilities=profile.capabilities,
        notes=profile.notes,
    )


def build_openai_compatible_payload(config: ProviderConfig, request: ChatRequest) -> dict[str, Any]:
    """作用：
    构造 OpenAI-compatible 风格的请求预览。

    参数：
    config: 当前 provider 的运行时配置，主要使用其中的 `model`。
    request: 统一聊天请求对象，里面包含 messages 和常用采样参数。

    返回：
    一个普通字典，结构接近 OpenAI-compatible 平台的真实请求体。
    """
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": request.messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    if request.stop:
        payload["stop"] = request.stop
    if request.metadata:
        payload["metadata"] = request.metadata
    return payload


def build_claude_preview(config: ProviderConfig, request: ChatRequest) -> dict[str, Any]:
    """作用：
    构造 Claude 风格的请求预览，突出 system 字段独立传递这一差异。

    参数：
    config: 当前 provider 配置，主要使用其中的模型名。
    request: 统一聊天请求对象，函数会从中拆分 system 消息和普通消息。

    返回：
    一个适合教学展示的 Claude 风格 payload 预览。
    """
    # Claude 风格的关键差异是：
    # system 往往不是 messages[0]，而是被提升到独立字段。
    system_parts = [item["content"] for item in request.messages if item["role"] == "system"]
    content_messages = [item for item in request.messages if item["role"] != "system"]
    payload: dict[str, Any] = {
        "model": config.model,
        "system": "\n".join(system_parts) if system_parts else None,
        "messages": content_messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }
    if request.stop:
        payload["stop_sequences"] = request.stop
    return payload


def build_gemini_preview(config: ProviderConfig, request: ChatRequest) -> dict[str, Any]:
    """作用：
    构造 Gemini 风格的请求预览，展示 `parts` 和 `generationConfig` 的组织方式。

    参数：
    config: 当前 provider 配置，主要使用模型名。
    request: 统一聊天请求对象，函数会把 `messages` 转成 Gemini 风格的 `contents`。

    返回：
    一个适合教学展示的 Gemini 风格 payload 预览。
    """
    # Gemini 风格的关键差异是：
    # 文本内容常常要被组织到 parts 中，而不是直接放在 content 字符串里。
    system_parts = [item["content"] for item in request.messages if item["role"] == "system"]
    contents = []
    for item in request.messages:
        if item["role"] == "system":
            continue
        role = "user" if item["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["content"]}]})

    payload = {
        "model": config.model,
        "systemInstruction": {"parts": [{"text": "\n".join(system_parts)}]} if system_parts else None,
        "contents": contents,
        "generationConfig": {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        },
    }
    return payload


def build_provider_preview(config: ProviderConfig, request: ChatRequest) -> dict[str, Any]:
    """作用：
    根据 provider 类型，把统一的 `ChatRequest` 转成对应平台风格的请求预览。

    参数：
    config: 当前 provider 配置，决定走哪一种 payload 组织方式。
    request: 统一聊天请求对象。

    返回：
    一个按当前 provider 风格整理好的请求预览字典。
    """
    # 这里不做真实调用，只负责“统一输入 -> 平台风格预览”的转换。
    if config.provider_type == "openai_compatible":
        return build_openai_compatible_payload(config, request)
    if config.provider_type == "anthropic_style":
        return build_claude_preview(config, request)
    return build_gemini_preview(config, request)


def compare_provider_payloads(request: ChatRequest, providers: list[str]) -> dict[str, dict[str, Any]]:
    """作用：
    批量比较同一份请求在多个 provider 下的 payload 预览差异。

    参数：
    request: 要比较的统一聊天请求对象。
    providers: 需要比较的 provider 名称列表。

    返回：
    一个字典，key 是 provider 名，value 是对应的请求预览。
    """
    result: dict[str, dict[str, Any]] = {}
    for provider in providers:
        config = load_provider_config(provider)
        result[provider] = build_provider_preview(config, request)
    return result


def get_provider_status_rows() -> list[dict[str, Any]]:
    """作用：
    把 provider 注册表整理成更适合打印展示的“状态行”列表。

    参数：
    无。函数会遍历所有已注册 provider，并读取其能力矩阵和运行时配置。

    返回：
    一个列表，元素是适合表格式输出的普通字典。
    """
    rows: list[dict[str, Any]] = []
    for key in list_registered_providers():
        config = load_provider_config(key)
        rows.append(
            {
                "provider": key,
                "display_name": config.display_name,
                "type": config.provider_type,
                "ready": config.is_ready,
                "openai_compatible": config.capabilities.openai_compatible,
                "streaming": config.capabilities.supports_streaming,
                "structured": config.capabilities.supports_native_structured_output,
                "vision": config.capabilities.supports_vision,
                "model": config.model,
                "base_url": config.base_url,
            }
        )
    return rows


def mock_chat_response(config: ProviderConfig, request: ChatRequest, error: str | None = None) -> NormalizedChatResponse:
    """作用：
    构造一个统一格式的 mock 响应，保证教学示例在离线或环境不完整时仍能跑通。

    参数：
    config: 当前 provider 配置，用于保留平台信息。
    request: 当前聊天请求对象，函数会提取最后一条 user 消息做演示。
    error: 可选错误说明。
        常见用途是记录“为什么回退到了 mock 模式”。

    返回：
    一个 `NormalizedChatResponse`，其中 `mocked=True`。
    """
    last_user = ""
    for item in reversed(request.messages):
        if item["role"] == "user":
            last_user = item["content"]
            break

    content = (
        f"[MOCK:{config.key}] display_name={config.display_name}\n"
        f"provider_type={config.provider_type}\n"
        f"model={config.model}\n"
        f"last_user={last_user}"
    )
    return NormalizedChatResponse(
        provider=config.key,
        model=config.model,
        content=content,
        finish_reason="stop",
        request_preview=build_provider_preview(config, request),
        raw_response_preview={
            "id": "mock-chat-001",
            "provider": config.key,
            "model": config.model,
            "content": content,
        },
        mocked=True,
        elapsed_ms=0.0,
        error=error,
    )


def call_openai_compatible_chat(
    config: ProviderConfig,
    request: ChatRequest,
    timeout: float = 30.0,
) -> NormalizedChatResponse:
    """作用：
    发起一次 OpenAI-compatible 聊天请求，并把响应整理成统一结构。

    参数：
    config: 当前 provider 配置，包含认证信息、base_url 和模型名。
    request: 当前聊天请求对象，包含 messages、temperature、max_tokens 等参数。
    timeout: 单次请求超时秒数，默认 `30.0`。

    返回：
    一个 `NormalizedChatResponse`，上层代码可统一读取 content、usage 和调试信息。
    """
    # 第 1 步：先整理请求预览。
    # 即使真实调用失败，上层也仍然可以看到“原本准备发什么”。
    request_preview = build_provider_preview(config, request)
    start = time.time()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    # 第 2 步：初始化 OpenAI-compatible client。
    # 第二章只对 OpenAI-compatible 平台做真实调用，其他平台先保留扩展位。
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    # 第 3 步：发起真实请求，把统一的 ChatRequest 落到具体 SDK 调用上。
    response = client.chat.completions.create(
        model=config.model,
        messages=request.messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stop=request.stop,
        timeout=timeout,
    )
    # 第 4 步：提取 usage，避免把原始 SDK 对象直接传到业务层。
    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    # 第 5 步：提取最关键的回复内容和 finish_reason。
    message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason
    # 第 6 步：整理出更适合教学展示的响应预览。
    raw_preview = {
        "id": response.id,
        "model": response.model,
        "choices": [
            {
                "index": response.choices[0].index,
                "finish_reason": finish_reason,
                "message": {
                    "role": message.role,
                    "content": message.content,
                },
            }
        ],
        "usage": asdict(usage) if usage else None,
    }
    return NormalizedChatResponse(
        provider=config.key,
        model=config.model,
        content=message.content or "",
        usage=usage,
        finish_reason=finish_reason,
        request_preview=request_preview,
        raw_response_preview=raw_preview,
        mocked=False,
        elapsed_ms=(time.time() - start) * 1000,
    )


class UnifiedLLMClient:
    """
    第二章的最小统一客户端

    目标：
    - 统一 provider 配置加载
    - 统一 messages 级接口
    - 统一响应对象
    - 统一 debug / retry / timeout 行为
    - 非 OpenAI-compatible provider 先保留扩展位
    """

    def __init__(
        self,
        provider: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        debug: bool = True,
    ):
        """作用：
        初始化统一客户端，绑定 provider、超时、重试和调试开关。

        参数：
        provider: 初始 provider 名称。
            - 传入时使用指定 provider
            - 不传时读取默认 provider
        timeout: 单次真实调用的超时秒数。
        max_retries: 最多重试次数。
        debug: 是否打印请求前后的调试信息。
        """
        self.config = load_provider_config(provider)
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

    def switch_provider(self, provider: str) -> None:
        """作用：
        切换当前客户端绑定的 provider。

        参数：
        provider: 目标 provider 名称，例如 `bailian`、`deepseek`、`claude`。
        """
        self.config = load_provider_config(provider)

    def describe(self) -> dict[str, Any]:
        """作用：
        返回当前客户端的关键配置描述，方便调试和教学展示。

        参数：
        无。函数直接读取当前客户端持有的 `self.config`。

        返回：
        一个普通字典，包含 provider、model、ready 状态和能力矩阵。
        """
        return {
            "provider": self.config.key,
            "display_name": self.config.display_name,
            "provider_type": self.config.provider_type,
            "base_url": self.config.base_url,
            "model": self.config.model,
            "ready": self.config.is_ready,
            "notes": self.config.notes,
            "capabilities": asdict(self.config.capabilities),
        }

    def _debug_print_result(self, result: NormalizedChatResponse) -> None:
        """作用：
        在 debug 模式下统一打印调用结果，保证真实调用和 mock 回退都有一致的返回日志。

        参数：
        result: 本轮调用得到的统一响应对象。
        """
        print(
            "[DEBUG] chat.result "
            f"provider={result.provider} "
            f"model={result.model} "
            f"mocked={result.mocked} "
            f"finish_reason={result.finish_reason or '（未返回）'} "
            f"elapsed_ms={result.elapsed_ms} "
            f"error={result.error}"
        )
        print("[DEBUG] raw_response_preview:")
        print(json.dumps(result.raw_response_preview or {}, ensure_ascii=False, indent=2))

    def chat(self, request: ChatRequest) -> NormalizedChatResponse:
        """作用：
        作为统一聊天入口，对外提供稳定的 `client.chat(request)` 调用方式。

        参数：
        request: 统一聊天请求对象。

        返回：
        一个统一结构的 `NormalizedChatResponse`。
        """
        # debug 模式下，先打印一次紧凑摘要，再展开 request_preview。
        # 这样既能看到关键上下文，又不会和上层演示脚本重复太多信息。
        if self.debug:
            print(
                "[DEBUG] chat.start "
                f"provider={self.config.key} "
                f"model={self.config.model} "
                f"type={self.config.provider_type} "
                f"ready={self.config.is_ready}"
            )
            print("[DEBUG] request_preview:")
            print(json.dumps(build_provider_preview(self.config, request), ensure_ascii=False, indent=2))

        # 第二章的真实调用先只覆盖 OpenAI-compatible 平台；
        # 非兼容平台先统一返回 mock 结果，保留后续章节扩展位。
        if self.config.provider_type == "openai_compatible":
            result = self._chat_openai_compatible_with_retry(request)
        else:
            if self.debug:
                print(
                    "[DEBUG] mock_fallback "
                    f"provider={self.config.key} "
                    "reason=provider_not_openai_compatible"
                )
            result = mock_chat_response(
                self.config,
                request,
                error="当前 provider 不是 OpenAI-compatible，本章仅保留扩展位预览。",
            )

        if self.debug:
            self._debug_print_result(result)
        return result

    def _chat_openai_compatible_with_retry(self, request: ChatRequest) -> NormalizedChatResponse:
        """作用：
        对 OpenAI-compatible 平台执行带重试的真实调用，并在失败时自动回退 mock。

        参数：
        request: 当前聊天请求对象。

        返回：
        一个统一结构的 `NormalizedChatResponse`。
        """
        # 环境未就绪时，不直接抛错退出，而是回退 mock，让演示流程继续。
        if not self.config.is_ready:
            if self.debug:
                print(
                    "[DEBUG] mock_fallback "
                    f"provider={self.config.key} "
                    "reason=missing_required_env"
                )
            return mock_chat_response(
                self.config,
                request,
                error="未检测到完整环境变量，自动进入 mock 模式。",
            )

        last_error = ""
        # 这里做的是最小重试策略：
        # 失败后按 1s、2s、4s... 退避，最后一次仍失败则回退到 mock。
        for attempt in range(self.max_retries):
            try:
                if self.debug:
                    print(f"[DEBUG] attempt={attempt + 1} provider={self.config.key}")
                return call_openai_compatible_chat(
                    self.config,
                    request,
                    timeout=self.timeout,
                )
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if self.debug:
                    print(f"[DEBUG] request_failed={last_error}")
                if attempt == self.max_retries - 1:
                    break
                time.sleep(2 ** attempt)

        if self.debug:
            print(
                "[DEBUG] mock_fallback "
                f"provider={self.config.key} "
                "reason=request_failed_after_retries"
            )
        return mock_chat_response(
            self.config,
            request,
            error=f"真实调用失败，回退 mock 模式。last_error={last_error}",
        )
