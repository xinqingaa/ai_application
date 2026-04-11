"""
集中管理 foundation_lab 的基础配置。

当前阶段先用一个轻量 dataclass 收敛环境变量读取逻辑，避免配置分散到
脚本、服务层和客户端内部。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """保存项目运行所需的最小配置。"""

    app_name: str = "foundation_lab"
    app_version: str = "0.1.0"
    provider: str = "mock"
    model: str = "mock-gpt-foundation"
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.2
    max_tokens: int = 400
    timeout_seconds: float = 30.0
    retry_count: int = 1
    enable_streaming: bool = True
    use_mock_when_unconfigured: bool = True


def get_settings() -> Settings:
    """从环境变量读取配置，并在缺省时回退到适合教学阶段的默认值。"""

    return Settings(
        provider=os.getenv("FOUNDATION_LAB_PROVIDER", "mock"),
        model=os.getenv("FOUNDATION_LAB_MODEL", "mock-gpt-foundation"),
        api_key=os.getenv("OPENAI_API_KEY") or os.getenv("FOUNDATION_LAB_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("FOUNDATION_LAB_BASE_URL"),
        temperature=float(os.getenv("FOUNDATION_LAB_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("FOUNDATION_LAB_MAX_TOKENS", "400")),
        timeout_seconds=float(os.getenv("FOUNDATION_LAB_TIMEOUT_SECONDS", "30")),
        retry_count=int(os.getenv("FOUNDATION_LAB_RETRY_COUNT", "1")),
        enable_streaming=os.getenv("FOUNDATION_LAB_ENABLE_STREAMING", "true").lower() == "true",
        use_mock_when_unconfigured=os.getenv("FOUNDATION_LAB_USE_MOCK", "true").lower() == "true",
    )
