"""
provider_utils.py
第二章公共工具：provider 注册表、能力矩阵、请求预览、统一响应结构、最小统一客户端
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any


def load_env_if_possible() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


@dataclass
class ProviderCapabilities:
    openai_compatible: bool
    supports_system_role_inline: bool
    supports_separate_system_prompt: bool
    supports_streaming: bool
    supports_native_structured_output: bool
    supports_vision: bool


@dataclass
class ProviderProfile:
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
        if self.provider_type == "openai_compatible":
            return bool(self.api_key and self.base_url and self.model)
        return bool(self.api_key)


@dataclass
class ChatRequest:
    messages: list[dict[str, str]]
    temperature: float = 0.3
    max_tokens: int = 300
    stop: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class NormalizedChatResponse:
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
    return list(PROVIDER_REGISTRY.keys())


def load_provider_config(provider: str | None = None) -> ProviderConfig:
    key = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    profile = PROVIDER_REGISTRY.get(key, PROVIDER_REGISTRY["bailian"])
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
    if config.provider_type == "openai_compatible":
        return build_openai_compatible_payload(config, request)
    if config.provider_type == "anthropic_style":
        return build_claude_preview(config, request)
    return build_gemini_preview(config, request)


def compare_provider_payloads(request: ChatRequest, providers: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for provider in providers:
        config = load_provider_config(provider)
        result[provider] = build_provider_preview(config, request)
    return result


def get_provider_status_rows() -> list[dict[str, Any]]:
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
    start = time.time()
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("未安装 openai SDK，请先执行：pip install openai") from exc

    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    response = client.chat.completions.create(
        model=config.model,
        messages=request.messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stop=request.stop,
        timeout=timeout,
    )
    usage = None
    if response.usage:
        usage = ChatUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

    message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason
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
        request_preview=build_provider_preview(config, request),
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
        debug: bool = False,
    ):
        self.config = load_provider_config(provider)
        self.timeout = timeout
        self.max_retries = max_retries
        self.debug = debug

    def switch_provider(self, provider: str) -> None:
        self.config = load_provider_config(provider)

    def describe(self) -> dict[str, Any]:
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

    def chat(self, request: ChatRequest) -> NormalizedChatResponse:
        if self.debug:
            print("[DEBUG] current_client_config:")
            print(json.dumps(self.describe(), ensure_ascii=False, indent=2))
            print("[DEBUG] request_preview:")
            print(json.dumps(build_provider_preview(self.config, request), ensure_ascii=False, indent=2))

        if self.config.provider_type == "openai_compatible":
            return self._chat_openai_compatible_with_retry(request)
        return mock_chat_response(
            self.config,
            request,
            error="当前 provider 不是 OpenAI-compatible，本章仅保留扩展位预览。",
        )

    def _chat_openai_compatible_with_retry(self, request: ChatRequest) -> NormalizedChatResponse:
        if not self.config.is_ready:
            return mock_chat_response(
                self.config,
                request,
                error="未检测到完整环境变量，自动进入 mock 模式。",
            )

        last_error = ""
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

        return mock_chat_response(
            self.config,
            request,
            error=f"真实调用失败，回退 mock 模式。last_error={last_error}",
        )
