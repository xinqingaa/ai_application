from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
import time
from typing import Any, Protocol


def load_env_if_possible() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


@dataclass(frozen=True)
class GenerationProviderProfile:
    key: str
    display_name: str
    api_key_env: str
    base_url_env: str
    model_env: str
    default_base_url: str
    default_model: str


@dataclass(frozen=True)
class GenerationUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class GenerationResult:
    provider: str
    model: str
    content: str
    usage: GenerationUsage | None = None
    finish_reason: str | None = None
    request_preview: dict[str, Any] | None = None
    raw_response_preview: dict[str, Any] | None = None
    mocked: bool = False
    error: str | None = None
    used_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class GenerationProviderConfig:
    key: str
    display_name: str
    api_key_env: str
    base_url_env: str
    model_env: str
    api_key: str | None
    base_url: str | None
    model: str
    temperature: float = 0.0
    max_tokens: int = 280

    @property
    def is_ready(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)


class LLMClient(Protocol):
    def describe(self) -> dict[str, Any]:
        ...

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        ...


GENERATION_PROVIDER_REGISTRY: dict[str, GenerationProviderProfile] = {
    "openai": GenerationProviderProfile(
        key="openai",
        display_name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        model_env="OPENAI_MODEL",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
    ),
    "bailian": GenerationProviderProfile(
        key="bailian",
        display_name="Bailian / Qwen",
        api_key_env="BAILIAN_API_KEY",
        base_url_env="BAILIAN_BASE_URL",
        model_env="BAILIAN_MODEL",
        default_base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
    ),
    "deepseek": GenerationProviderProfile(
        key="deepseek",
        display_name="DeepSeek",
        api_key_env="DEEPSEEK_API_KEY",
        base_url_env="DEEPSEEK_BASE_URL",
        model_env="DEEPSEEK_MODEL",
        default_base_url="https://api.deepseek.com",
        default_model="deepseek-chat",
    ),
    "glm": GenerationProviderProfile(
        key="glm",
        display_name="GLM",
        api_key_env="GLM_API_KEY",
        base_url_env="GLM_BASE_URL",
        model_env="GLM_MODEL",
        default_base_url="https://open.bigmodel.cn/api/paas/v4/",
        default_model="glm-4.5-air",
    ),
}


def load_generation_provider_config(
    provider: str | None = None,
    *,
    temperature: float = 0.0,
    max_tokens: int = 280,
) -> GenerationProviderConfig:
    key = (provider or os.getenv("DEFAULT_PROVIDER", "bailian")).strip().lower()
    profile = GENERATION_PROVIDER_REGISTRY.get(key, GENERATION_PROVIDER_REGISTRY["bailian"])
    api_key = os.getenv(profile.api_key_env)
    base_url = os.getenv(profile.base_url_env, profile.default_base_url)
    model = os.getenv(profile.model_env, profile.default_model)
    return GenerationProviderConfig(
        key=profile.key,
        display_name=profile.display_name,
        api_key_env=profile.api_key_env,
        base_url_env=profile.base_url_env,
        model_env=profile.model_env,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def missing_generation_fields(config: GenerationProviderConfig) -> list[str]:
    missing: list[str] = []
    if not config.api_key:
        missing.append(config.api_key_env)
    if not config.base_url:
        missing.append(config.base_url_env)
    if not config.model:
        missing.append(config.model_env)
    return missing


def build_openai_compatible_preview(
    config: GenerationProviderConfig,
    messages: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "provider": config.key,
        "display_name": config.display_name,
        "base_url": config.base_url,
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }


@dataclass
class OpenAICompatibleLLMClient:
    config: GenerationProviderConfig
    timeout: float = 20.0
    max_retries: int = 0

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.config.key,
            "display_name": self.config.display_name,
            "base_url": self.config.base_url,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "ready": self.config.is_ready,
            "mocked": False,
        }

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        request_preview = build_openai_compatible_preview(self.config, messages)
        start = time.time()
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "未安装 openai SDK，请先执行：python -m pip install openai"
            ) from exc

        client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )
        response = client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        message = response.choices[0].message.content or ""
        usage = None
        if response.usage is not None:
            usage = GenerationUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        raw_response_preview = {
            "id": response.id,
            "model": response.model,
            "choices": [
                {
                    "index": response.choices[0].index,
                    "finish_reason": response.choices[0].finish_reason,
                    "message": {
                        "role": response.choices[0].message.role,
                        "content": message[:300],
                    },
                }
            ],
            "usage": asdict(usage) if usage else None,
            "elapsed_ms": round((time.time() - start) * 1000, 2),
        }
        return GenerationResult(
            provider=self.config.key,
            model=self.config.model,
            content=message.strip(),
            usage=usage,
            finish_reason=response.choices[0].finish_reason,
            request_preview=request_preview,
            raw_response_preview=raw_response_preview,
            mocked=False,
        )
